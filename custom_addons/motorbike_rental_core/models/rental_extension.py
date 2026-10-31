import math

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


_RENTAL_EXTENSION_LOCK_NAMESPACE = 0x52455854


class RentalExtension(models.Model):
    _name = 'rental.extension'
    _description = 'Yêu cầu gia hạn thuê xe'
    _order = 'requested_at desc, id desc'

    name = fields.Char(
        string='Mã yêu cầu',
        required=True,
        readonly=True,
        copy=False,
        default='/',
    )
    contract_id = fields.Many2one(
        'rental.contract',
        string='Hợp đồng',
        required=True,
        ondelete='restrict',
        index=True,
    )
    customer_id = fields.Many2one(
        related='contract_id.customer_id',
        string='Khách hàng',
        readonly=True,
    )
    currency_id = fields.Many2one(
        related='contract_id.currency_id',
        string='Tiền tệ',
        readonly=True,
    )
    original_end_date = fields.Datetime(
        string='Thời gian trả hiện tại',
        required=True,
        readonly=True,
        copy=False,
    )
    original_rental_days = fields.Integer(
        string='Số ngày thuê hiện tại',
        required=True,
        readonly=True,
        copy=False,
    )
    requested_end_date = fields.Datetime(
        string='Thời gian trả đề nghị',
        required=True,
        copy=False,
    )
    additional_days = fields.Integer(
        string='Số ngày tăng thêm',
        compute='_compute_additional_amount',
        store=True,
    )
    additional_amount = fields.Monetary(
        string='Tiền thuê tăng thêm',
        compute='_compute_additional_amount',
        store=True,
        currency_field='currency_id',
    )
    reason = fields.Text(string='Lý do gia hạn', required=True)
    state = fields.Selection(
        [
            ('pending', 'Chờ kiểm tra'),
            ('approved', 'Đã gia hạn'),
            ('rejected', 'Từ chối'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='pending',
        readonly=True,
        copy=False,
        index=True,
    )
    requested_by = fields.Many2one(
        'res.users',
        string='Người tạo yêu cầu',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
    )
    requested_at = fields.Datetime(
        string='Thời điểm yêu cầu',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
    )
    reviewed_by = fields.Many2one(
        'res.users', string='Người kiểm tra/xử lý', readonly=True, copy=False
    )
    reviewed_at = fields.Datetime(
        string='Thời điểm xử lý', readonly=True, copy=False
    )
    rejection_reason = fields.Text(string='Lý do từ chối')

    def _lock_contract(self, contract):
        contract.flush_recordset(['state', 'end_date', 'rental_days'])
        self.env.cr.execute(
            'SELECT id FROM rental_contract WHERE id = %s FOR UPDATE',
            (contract.id,),
        )
        contract.invalidate_recordset(['state', 'end_date', 'rental_days'])

    def _lock_extension(self):
        self.ensure_one()
        self.flush_recordset(['state'])
        self.env.cr.execute(
            'SELECT id FROM rental_extension WHERE id = %s FOR UPDATE',
            (self.id,),
        )
        self.invalidate_recordset(['state'])

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        contract_id = (
            defaults.get('contract_id')
            or self.env.context.get('default_contract_id')
        )
        if not contract_id:
            return defaults

        contract = self.env['rental.contract'].browse(contract_id).exists()
        if not contract:
            return defaults
        if contract.state != 'in_progress':
            raise UserError(_('Chỉ hợp đồng đang thuê mới có thể yêu cầu gia hạn.'))

        if 'original_end_date' in fields_list:
            defaults['original_end_date'] = contract.end_date
        if 'original_rental_days' in fields_list:
            defaults['original_rental_days'] = contract.rental_days
        if (
            'requested_end_date' in fields_list
            and not defaults.get('requested_end_date')
        ):
            defaults['requested_end_date'] = fields.Datetime.add(
                contract.end_date, days=1
            )
        return defaults

    @api.model_create_multi
    def create(self, vals_list):
        seen_contract_ids = set()
        for vals in vals_list:
            contract_id = (
                vals.get('contract_id')
                or self.env.context.get('default_contract_id')
            )
            contract = self.env['rental.contract'].browse(contract_id).exists()
            if not contract:
                raise ValidationError(_('Vui lòng chọn hợp đồng cần gia hạn.'))
            vals['contract_id'] = contract.id
            self._lock_contract(contract)
            if contract.state != 'in_progress':
                raise UserError(_('Chỉ hợp đồng đang thuê mới có thể yêu cầu gia hạn.'))
            if vals.get('state', 'pending') != 'pending':
                raise UserError(_('Yêu cầu gia hạn mới phải ở trạng thái Chờ kiểm tra.'))
            if contract.id in seen_contract_ids:
                raise UserError(
                    _('Chỉ được tạo một yêu cầu gia hạn chờ xử lý cho mỗi hợp đồng.')
                )
            seen_contract_ids.add(contract.id)

            self.env.cr.execute(
                'SELECT pg_advisory_xact_lock(%s, %s)',
                (_RENTAL_EXTENSION_LOCK_NAMESPACE, contract.id),
            )
            pending_request = self.search(
                [('contract_id', '=', contract.id), ('state', '=', 'pending')],
                limit=1,
            )
            if pending_request:
                raise UserError(
                    _('Hợp đồng này đang có một yêu cầu gia hạn chờ xử lý.')
                )
            vals.update({
                'name': (
                    self.env['ir.sequence'].next_by_code('rental.extension')
                    or '/'
                ),
                'original_end_date': contract.end_date,
                'original_rental_days': contract.rental_days,
                'requested_by': self.env.user.id,
                'requested_at': fields.Datetime.now(),
            })
            for readonly_field in (
                'reviewed_by', 'reviewed_at', 'rejection_reason'
            ):
                vals.pop(readonly_field, None)
        return super().create(vals_list)

    @api.depends(
        'requested_end_date',
        'original_rental_days',
        'contract_id.start_date',
        'contract_id.line_ids.daily_rate',
        'currency_id',
    )
    def _compute_additional_amount(self):
        for extension in self:
            additional_days = 0
            additional_amount = 0
            if (
                extension.requested_end_date
                and extension.contract_id.start_date
                and extension.original_end_date
            ):
                seconds = (
                    extension.requested_end_date - extension.contract_id.start_date
                ).total_seconds()
                requested_days = max(1, math.ceil(seconds / 86400)) if seconds > 0 else 0
                additional_days = max(
                    0, requested_days - extension.original_rental_days
                )
                additional_amount = sum(
                    extension.contract_id.line_ids.mapped('daily_rate')
                ) * additional_days
                if extension.currency_id:
                    additional_amount = extension.currency_id.round(additional_amount)
            extension.additional_days = additional_days
            extension.additional_amount = additional_amount

    @api.constrains('requested_end_date', 'original_end_date')
    def _check_requested_end_date(self):
        for extension in self:
            if (
                extension.requested_end_date
                and extension.original_end_date
                and extension.requested_end_date <= extension.original_end_date
            ):
                raise ValidationError(
                    _('Thời gian trả đề nghị phải sau thời gian trả hiện tại.')
                )

    def write(self, vals):
        editable_fields = {'requested_end_date', 'reason', 'rejection_reason'}
        if not vals or set(vals) - editable_fields:
            raise UserError(
                _('Không được sửa trực tiếp yêu cầu gia hạn; hãy dùng các nút xử lý.')
            )
        if self.filtered(lambda extension: extension.state != 'pending'):
            raise UserError(_('Chỉ yêu cầu đang chờ kiểm tra mới được chỉnh sửa.'))
        if self.env.user.has_group('motorbike_rental_core.group_rental_manager'):
            return super().write(vals)
        if set(vals) - {'requested_end_date', 'reason'} or self.filtered(
            lambda extension: extension.requested_by != self.env.user
        ):
            raise UserError(
                _('Chỉ người tạo yêu cầu mới được cập nhật đề nghị đang chờ kiểm tra.')
            )
        return super().write(vals)

    def _check_manager(self):
        if not self.env.user.has_group('motorbike_rental_core.group_rental_manager'):
            raise UserError(_('Chỉ quản lý thuê xe mới được từ chối yêu cầu.'))

    def action_check_and_extend(self):
        for extension in self:
            extension._lock_extension()
            if extension.state != 'pending':
                raise UserError(_('Chỉ yêu cầu đang chờ kiểm tra mới được xử lý.'))
            contract = extension.contract_id
            self._lock_contract(contract)
            if contract.state != 'in_progress':
                raise UserError(
                    _('Chỉ hợp đồng đang thuê mới có thể gia hạn.')
                )
            if contract.end_date != extension.original_end_date:
                raise UserError(
                    _(
                        'Thời gian kết thúc hợp đồng đã thay đổi sau khi tạo yêu cầu. '
                        'Vui lòng tạo yêu cầu gia hạn mới.'
                    )
                )

            contract._check_vehicle_availability(
                end_date=extension.requested_end_date
            )
            super(RentalExtension, extension).write({
                'state': 'approved',
                'reviewed_by': self.env.user.id,
                'reviewed_at': fields.Datetime.now(),
            })
            contract.with_context(
                rental_extension_id=extension.id
            ).write({'end_date': extension.requested_end_date})
            extension._sync_operation_schedule()
        return {'type': 'ir.actions.act_window_close'}

    def action_reject(self):
        self._check_manager()
        for extension in self:
            extension._lock_extension()
            if extension.state != 'pending':
                raise UserError(_('Chỉ yêu cầu đang chờ kiểm tra mới được xử lý.'))
            if not (extension.rejection_reason or '').strip():
                raise UserError(_('Vui lòng nhập lý do từ chối.'))
            super(RentalExtension, extension).write({
                'state': 'rejected',
                'reviewed_by': self.env.user.id,
                'reviewed_at': fields.Datetime.now(),
            })
        return True

    def action_cancel(self):
        for extension in self:
            extension._lock_extension()
            if extension.state != 'pending':
                raise UserError(_('Chỉ yêu cầu đang chờ kiểm tra mới có thể hủy.'))
            if (
                extension.requested_by != self.env.user
                and not self.env.user.has_group(
                    'motorbike_rental_core.group_rental_manager'
                )
            ):
                raise UserError(_('Chỉ người tạo yêu cầu hoặc quản lý mới được hủy.'))
            super(RentalExtension, extension).write({
                'state': 'cancelled',
                'reviewed_by': self.env.user.id,
                'reviewed_at': fields.Datetime.now(),
            })
        return True

    def _sync_operation_schedule(self):
        self.ensure_one()
        if 'rental.operation.ticket.vehicle' not in self.env.registry:
            return
        ticket_model = self.env['rental.operation.ticket']
        if 'contract_id' not in ticket_model._fields:
            return
        tickets = ticket_model.sudo().search(
            [('contract_id', '=', self.contract_id.id)]
        )
        vehicle_model = self.env['rental.operation.ticket.vehicle'].sudo()
        if not tickets or 'date_checkin' not in vehicle_model._fields:
            return
        vehicle_lines = vehicle_model.search([
            ('ticket_id', 'in', tickets.ids),
            ('status', '!=', 'returned'),
        ])
        vehicle_lines.write({'date_checkin': self.requested_end_date})

    def unlink(self):
        raise UserError(_('Không được xóa yêu cầu gia hạn để bảo toàn lịch sử.'))

import math
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RentalContract(models.Model):
    _name = 'rental.contract'
    _description = 'Hợp đồng thuê xe'
    _order = 'start_date desc, id desc'
    _sql_constraints = [
        (
            'valid_rental_date_range',
            'CHECK(end_date > start_date)',
            'Ngày kết thúc phải sau ngày bắt đầu.',
        ),
        (
            'nonnegative_rental_deposit',
            'CHECK(deposit_amount >= 0)',
            'Tiền đặt cọc không được âm.',
        ),
    ]

    name = fields.Char(string='Mã hợp đồng', required=True, copy=False, default='/')
    customer_id = fields.Many2one(
        'res.partner', string='Khách hàng', required=True, ondelete='restrict', index=True
    )
    start_date = fields.Datetime(
        string='Ngày giờ bắt đầu', required=True, default=fields.Datetime.now
    )
    end_date = fields.Datetime(
        string='Ngày giờ kết thúc',
        required=True,
        default=lambda self: fields.Datetime.add(fields.Datetime.now(), days=1),
    )
    rental_days = fields.Integer(string='Số ngày thuê', compute='_compute_rental_days', store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ', required=True,
        default=lambda self: self.env.company.currency_id,
    )
    deposit_amount = fields.Monetary(
        string='Tiền đặt cọc', required=True, default=0, currency_field='currency_id'
    )
    line_ids = fields.One2many(
        'rental.contract.line', 'contract_id', string='Xe thuê', copy=True
    )
    total_amount = fields.Monetary(
        string='Tổng tiền thuê',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id',
    )
    state = fields.Selection(
        [
            ('draft', 'Nháp'),
            ('confirmed', 'Đã xác nhận'),
            ('in_progress', 'Đang thuê'),
            ('done', 'Hoàn tất'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        required=True,
        default='draft',
        copy=False,
        index=True,
    )
    notes = fields.Text(string='Ghi chú')

    @api.depends('start_date', 'end_date')
    def _compute_rental_days(self):
        for contract in self:
            days = 0
            if contract.start_date and contract.end_date:
                seconds = (contract.end_date - contract.start_date).total_seconds()
                if seconds > 0:
                    days = max(1, math.ceil(seconds / 86400))
            contract.rental_days = max(days, 0)

    @api.depends('line_ids.subtotal', 'currency_id')
    def _compute_total_amount(self):
        for contract in self:
            total = sum(contract.line_ids.mapped('subtotal'))
            contract.total_amount = (
                contract.currency_id.round(total) if contract.currency_id else total
            )

    @api.model_create_multi
    def create(self, vals_list):
        default_state = self.default_get(['state']).get('state', 'draft')
        for vals in vals_list:
            if vals.get('deposit_amount', 0) < 0:
                raise ValidationError(_('Tiền đặt cọc không được âm.'))
            if vals.get('state', default_state) != 'draft':
                raise UserError(_('Hợp đồng mới phải ở trạng thái Nháp.'))
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.contract') or '/'
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('deposit_amount', 0) < 0:
            raise ValidationError(_('Tiền đặt cọc không được âm.'))
        if set(vals) - {'state'}:
            locked_contract = self.filtered(lambda contract: contract.state != 'draft')
            if locked_contract:
                raise UserError(
                    _('Không thể chỉnh sửa hợp đồng sau khi đã xác nhận hoặc kết thúc.')
                )
        if 'state' in vals:
            transitions = {
                'draft': {'confirmed', 'cancelled'},
                'confirmed': {'in_progress', 'cancelled'},
                'in_progress': {'done', 'cancelled'},
                'done': set(),
                'cancelled': set(),
            }
            state_labels = dict(self._fields['state'].selection)
            for contract in self:
                target_state = vals['state']
                if (
                    target_state != contract.state
                    and target_state not in transitions.get(contract.state, set())
                ):
                    raise UserError(
                        _('Không thể chuyển hợp đồng từ "%(current)s" sang "%(target)s".')
                        % {
                            'current': state_labels.get(contract.state, contract.state),
                            'target': state_labels.get(target_state, target_state),
                        }
                    )
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda contract: contract.state != 'draft'):
            raise UserError(
                _('Không thể xóa hợp đồng sau khi đã xác nhận hoặc kết thúc.')
            )
        return super().unlink()

    @api.constrains(
        'start_date', 'end_date', 'deposit_amount', 'state', 'line_ids'
    )
    def _check_rental_period(self):
        for contract in self:
            if contract.deposit_amount < 0:
                raise ValidationError(_('Tiền đặt cọc không được âm.'))
            if not contract.start_date or not contract.end_date:
                continue
            if contract.end_date <= contract.start_date:
                raise ValidationError(_('Ngày kết thúc phải sau ngày bắt đầu.'))
            if contract.state in ('confirmed', 'in_progress'):
                if not contract.line_ids:
                    raise ValidationError(_('Hợp đồng phải có ít nhất một xe để xác nhận.'))
                contract._check_vehicle_availability()

    def _check_vehicle_availability(self):
        self.ensure_one()
        vehicle_ids = self.line_ids.mapped('vehicle_id').ids
        if not vehicle_ids:
            return
        conflict = self.search(
            [
                ('id', '!=', self.id),
                ('state', 'in', ['confirmed', 'in_progress']),
                ('start_date', '<', self.end_date),
                ('end_date', '>', self.start_date),
                ('line_ids.vehicle_id', 'in', vehicle_ids),
            ],
            limit=1,
        )
        if conflict:
            conflict_line = self.env['rental.contract.line'].search(
                [
                    ('contract_id', '=', conflict.id),
                    ('vehicle_id', 'in', vehicle_ids),
                ],
                limit=1,
            )
            vehicle_name = conflict_line.vehicle_id.display_name or str(conflict_line.vehicle_id.id)
            raise ValidationError(
                _('Xe %s đã được giữ trong hợp đồng %s ở thời gian này.')
                % (vehicle_name, conflict.name)
            )

    def action_confirm(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError(_('Chỉ hợp đồng nháp mới có thể được xác nhận.'))
            contract.state = 'confirmed'

    def action_start(self):
        for contract in self:
            if contract.state != 'confirmed':
                raise UserError(_('Chỉ hợp đồng đã xác nhận mới có thể bắt đầu.'))
            contract.state = 'in_progress'

    def action_done(self):
        for contract in self:
            if contract.state != 'in_progress':
                raise UserError(_('Chỉ hợp đồng đang thuê mới có thể hoàn tất.'))
            contract.state = 'done'

    def action_cancel(self):
        for contract in self:
            if contract.state in ('done', 'cancelled'):
                raise UserError(_('Không thể hủy hợp đồng đã hoàn tất hoặc đã hủy.'))
            contract.state = 'cancelled'

class RentalContractLine(models.Model):
    _name = 'rental.contract.line'
    _description = 'Xe trong hợp đồng thuê'
    _order = 'id'

    contract_id = fields.Many2one(
        'rental.contract', string='Hợp đồng', required=True, ondelete='cascade', index=True
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Xe thuê',
        required=True,
        ondelete='restrict',
        index=True,
    )
    _sql_constraints = [
        (
            'unique_contract_vehicle',
            'UNIQUE(contract_id, vehicle_id)',
            'Mỗi xe chỉ được xuất hiện một lần trong một hợp đồng!',
        ),
        (
            'nonnegative_daily_rate',
            'CHECK(daily_rate >= 0)',
            'Giá thuê mỗi ngày không được âm.',
        ),
    ]
    vehicle_type_id = fields.Many2one(
        'rental.vehicle.type',
        string='Dòng xe / bảng giá',
        required=True,
        ondelete='restrict',
        domain=[('active', '=', True)],
    )
    vehicle_model_id = fields.Many2one(
        related='vehicle_type_id.model_id', string='Dòng xe', readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency', related='contract_id.currency_id', store=True, readonly=True
    )
    daily_rate = fields.Monetary(
        string='Giá thuê mỗi ngày', required=True, default=0, currency_field='currency_id'
    )
    subtotal = fields.Monetary(
        string='Thành tiền', compute='_compute_subtotal', store=True, currency_field='currency_id'
    )

    @api.depends('contract_id.rental_days', 'daily_rate', 'currency_id')
    def _compute_subtotal(self):
        for line in self:
            amount = line.contract_id.rental_days * line.daily_rate
            line.subtotal = line.currency_id.round(amount) if line.currency_id else amount

    @api.onchange('vehicle_type_id')
    def _onchange_vehicle_type_id(self):
        if self.vehicle_type_id:
            self.daily_rate = self.vehicle_type_id.daily_rate
            if (
                self.vehicle_id
                and self.vehicle_id.model_id != self.vehicle_type_id.model_id
            ):
                self.vehicle_id = False
            return {
                'domain': {
                    'vehicle_id': [
                        ('active', '=', True),
                        ('model_id', '=', self.vehicle_type_id.model_id.id),
                    ],
                },
            }
        return {'domain': {'vehicle_id': [('active', '=', True)]}}

    @api.model_create_multi
    def create(self, vals_list):
        default_contract_id = self.default_get(['contract_id']).get('contract_id')
        for vals in vals_list:
            contract_id = vals.get('contract_id', default_contract_id)
            contract = self.env['rental.contract'].browse(contract_id)
            if contract and contract.state != 'draft':
                raise UserError(
                    _('Không thể thêm xe vào hợp đồng sau khi đã xác nhận.')
                )
            if vals.get('vehicle_type_id') and 'daily_rate' not in vals:
                vehicle_type = self.env['rental.vehicle.type'].browse(vals['vehicle_type_id'])
                vals['daily_rate'] = vehicle_type.daily_rate
        return super().create(vals_list)

    def write(self, vals):
        contracts = self.mapped('contract_id')
        if vals.get('contract_id'):
            contracts |= self.env['rental.contract'].browse(vals['contract_id'])
        if contracts.filtered(lambda contract: contract.state != 'draft'):
            raise UserError(
                _('Không thể chỉnh sửa xe trong hợp đồng sau khi đã xác nhận.')
            )
        return super().write(vals)

    def unlink(self):
        if self.mapped('contract_id').filtered(
            lambda contract: contract.state != 'draft'
        ):
            raise UserError(
                _('Không thể xóa xe khỏi hợp đồng sau khi đã xác nhận.')
            )
        return super().unlink()

    @api.constrains('vehicle_id', 'vehicle_type_id', 'contract_id', 'daily_rate')
    def _check_vehicle_line(self):
        for line in self:
            if line.daily_rate < 0:
                raise ValidationError(_('Giá thuê mỗi ngày không được âm.'))
            if not line.vehicle_type_id or not line.contract_id:
                continue
            if not line.vehicle_id.active:
                raise ValidationError(_('Không thể cho thuê xe đã lưu trữ.'))
            if not line.vehicle_type_id.active:
                raise ValidationError(_('Không thể sử dụng bảng giá đã lưu trữ.'))
            if line.vehicle_id.model_id != line.vehicle_type_id.model_id:
                raise ValidationError(
                    _('Dòng xe của bảng giá phải trùng với dòng xe thực tế.')
                )
            if line.vehicle_type_id.currency_id != line.contract_id.currency_id:
                raise ValidationError(
                    _('Tiền tệ của dòng giá phải trùng với tiền tệ trên hợp đồng.')
                )
            duplicate = self.search(
                [
                    ('id', '!=', line.id),
                    ('contract_id', '=', line.contract_id.id),
                    ('vehicle_id', '=', line.vehicle_id.id),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(_('Không thể thêm cùng một xe hai lần vào hợp đồng.'))
            if line.contract_id.state in ('confirmed', 'in_progress'):
                line.contract_id._check_vehicle_availability()
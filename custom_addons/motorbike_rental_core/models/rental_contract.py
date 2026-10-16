import math
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RentalContract(models.Model):
    _name = 'rental.contract'
    _description = 'Hợp đồng thuê xe'
    _order = 'start_date desc, id desc'

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
    rental_days = fields.Integer(string='Số ngày thuê', compute='_compute_amounts', store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Tiền tệ', required=True,
        default=lambda self: self.env.company.currency_id,
    )
    deposit_amount = fields.Monetary(
        string='Tiền đặt cọc', required=True, default=0, currency_field='currency_id'
    )
    min_rental_days = fields.Integer(
        string='Số ngày thuê tối thiểu', required=True, default=1
    )
    max_rental_days = fields.Integer(
        string='Số ngày thuê tối đa',
        default=0,
        help='Để 0 nếu không giới hạn số ngày thuê.',
    )
    line_ids = fields.One2many(
        'rental.contract.line', 'contract_id', string='Xe thuê', copy=True
    )
    total_amount = fields.Monetary(
        string='Tổng tiền thuê', compute='_compute_amounts', store=True, currency_field='currency_id'
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

    @api.depends('start_date', 'end_date', 'line_ids.daily_rate')
    def _compute_amounts(self):
        for contract in self:
            days = 0
            if contract.start_date and contract.end_date:
                seconds = (contract.end_date - contract.start_date).total_seconds()
                if seconds > 0:
                    days = max(1, math.ceil(seconds / 86400))
            contract.rental_days = max(days, 0)
            contract.total_amount = contract.rental_days * sum(
                contract.line_ids.mapped('daily_rate')
            )

    @api.model_create_multi
    def create(self, vals_list):
        default_state = self.default_get(['state']).get('state', 'draft')
        for vals in vals_list:
            if vals.get('state', default_state) != 'draft':
                raise UserError(_('Hợp đồng mới phải ở trạng thái Nháp.'))
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.contract') or '/'
        return super().create(vals_list)

    def write(self, vals):
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

    @api.constrains(
        'start_date', 'end_date', 'min_rental_days', 'max_rental_days',
        'deposit_amount', 'state', 'line_ids'
    )
    def _check_rental_period(self):
        for contract in self:
            if contract.deposit_amount < 0:
                raise ValidationError(_('Tiền đặt cọc không được âm.'))
            if not contract.start_date or not contract.end_date:
                continue
            if contract.min_rental_days < 1:
                raise ValidationError(_('Số ngày thuê tối thiểu phải từ 1 trở lên.'))
            if contract.max_rental_days and contract.max_rental_days < contract.min_rental_days:
                raise ValidationError(
                    _('Số ngày thuê tối đa phải lớn hơn hoặc bằng số ngày tối thiểu.')
                )
            if contract.end_date <= contract.start_date:
                raise ValidationError(_('Ngày kết thúc phải sau ngày bắt đầu.'))
            days = contract.rental_days
            if days < contract.min_rental_days:
                raise ValidationError(
                    _('Thời hạn thuê phải ít nhất %s ngày.') % contract.min_rental_days
                )
            if contract.max_rental_days and days > contract.max_rental_days:
                raise ValidationError(
                    _('Thời hạn thuê không được vượt quá %s ngày.') % contract.max_rental_days
                )
            if contract.state in ('confirmed', 'in_progress'):
                if not contract.line_ids:
                    raise ValidationError(_('Hợp đồng phải có ít nhất một xe để xác nhận.'))
                contract._check_vehicle_availability()

    def _check_vehicle_availability(self):
        self.ensure_one()
        vehicle_ids = self.line_ids.mapped('vehicle_id').ids
        if not vehicle_ids:
            return
        for eligibility in self.line_ids.mapped('vehicle_id').check_fleet_availability(
                self.start_date, self.end_date):
            if not eligibility['fleet_ok']:
                vehicle = self.env['fleet.vehicle'].browse(eligibility['vehicle_id'])
                raise ValidationError(_('Xe %s chưa đủ điều kiện khai thác: %s') % (
                    vehicle.display_name, ', '.join(eligibility['reasons'])))
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
        ('unique_contract_vehicle', 'UNIQUE(contract_id, vehicle_id)', 'Mỗi xe chỉ được xuất hiện một lần trong một hợp đồng!')
    ]
    vehicle_type_id = fields.Many2one(
        'rental.vehicle.type',
        string='Dòng xe / bảng giá',
        required=True,
        ondelete='restrict',
        domain=[('active', '=', True)],
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

    @api.depends('contract_id.rental_days', 'daily_rate')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.contract_id.rental_days * line.daily_rate

    @api.onchange('vehicle_type_id')
    def _onchange_vehicle_type_id(self):
        if self.vehicle_type_id:
            self.daily_rate = self.vehicle_type_id.daily_rate

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('vehicle_type_id') and 'daily_rate' not in vals:
                vehicle_type = self.env['rental.vehicle.type'].browse(vals['vehicle_type_id'])
                vals['daily_rate'] = vehicle_type.daily_rate
        return super().create(vals_list)

    @api.constrains('vehicle_id', 'vehicle_type_id', 'contract_id', 'daily_rate')
    def _check_vehicle_line(self):
        for line in self:
            if line.daily_rate < 0:
                raise ValidationError(_('Giá thuê mỗi ngày không được âm.'))
            if not line.vehicle_type_id or not line.contract_id:
                continue
            if line.vehicle_id.model_id != line.vehicle_type_id.model_id:
                raise ValidationError(_('Dòng giá phải đúng với dòng xe được chọn.'))
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

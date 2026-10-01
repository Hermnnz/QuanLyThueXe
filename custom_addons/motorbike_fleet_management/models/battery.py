from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MotorbikeBattery(models.Model):
    _name = 'motorbike.battery'
    _description = 'Pin xe điện'
    _rec_name = 'battery_code'
    _order = 'battery_code, id'

    battery_code = fields.Char('Mã pin', required=True, copy=False, index=True)
    serial_number = fields.Char('Serial', copy=False)
    capacity_kwh = fields.Float('Dung lượng (kWh)')
    voltage = fields.Float('Điện áp (V)')
    soc = fields.Float('SOC (%)')
    soh = fields.Float('SOH (%)', default=100)
    cycle_count = fields.Integer('Số chu kỳ sạc')
    status = fields.Selection([
        ('available', 'Sẵn sàng'), ('installed', 'Đã gắn'),
        ('charging', 'Đang sạc'), ('maintenance', 'Bảo dưỡng'), ('retired', 'Ngừng sử dụng'),
    ], default='available', required=True, string='Trạng thái')
    warranty_expiry = fields.Date('Hạn bảo hành')
    active = fields.Boolean(default=True)
    assignment_ids = fields.One2many('motorbike.battery.assignment', 'battery_id', string='Lịch sử gắn pin')
    current_vehicle_id = fields.Many2one('fleet.vehicle', compute='_compute_current_vehicle', string='Xe hiện tại')

    _code_unique = models.Constraint('UNIQUE(battery_code)', 'Mã pin phải duy nhất.')
    _serial_unique = models.Constraint('UNIQUE(serial_number)', 'Serial pin phải duy nhất.')

    @api.depends('assignment_ids.vehicle_id', 'assignment_ids.removed_at')
    def _compute_current_vehicle(self):
        for battery in self:
            current = battery.assignment_ids.filtered(lambda item: not item.removed_at)
            battery.current_vehicle_id = current[:1].vehicle_id

    @api.constrains('soc', 'soh', 'cycle_count', 'capacity_kwh', 'voltage')
    def _check_values(self):
        for battery in self:
            if not 0 <= battery.soc <= 100 or not 0 <= battery.soh <= 100:
                raise ValidationError(_('SOC và SOH phải từ 0–100%.'))
            if min(battery.cycle_count, battery.capacity_kwh, battery.voltage) < 0:
                raise ValidationError(_('Thông số pin không được âm.'))

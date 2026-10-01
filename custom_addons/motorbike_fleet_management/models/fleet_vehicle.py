from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_electric_motorbike = fields.Boolean('Xe máy điện', tracking=True)
    vehicle_code = fields.Char('Mã xe', copy=False, index=True)
    lifecycle_status = fields.Selection([
        ('active', 'Đang khai thác'), ('suspended', 'Tạm ngừng'),
        ('retired', 'Ngừng khai thác'),
    ], default='active', required=True, string='Vòng đời')
    operational_status = fields.Selection([
        ('available', 'Sẵn sàng'), ('rented', 'Đang thuê'),
        ('inspection', 'Chờ kiểm tra'), ('maintenance', 'Bảo dưỡng'),
    ], default='inspection', required=True, string='Trạng thái vận hành')
    technical_ready = fields.Boolean('Đạt điều kiện kỹ thuật', default=False)
    rental_blocked = fields.Boolean('Khóa thuê')
    block_reason = fields.Text('Lý do khóa')
    battery_assignment_ids = fields.One2many(
        'motorbike.battery.assignment', 'vehicle_id', string='Lịch sử pin')
    current_battery_id = fields.Many2one(
        'motorbike.battery', compute='_compute_current_battery', store=True,
        string='Pin hiện tại')
    current_soc = fields.Float(related='current_battery_id.soc', string='SOC (%)')
    current_soh = fields.Float(related='current_battery_id.soh', string='SOH (%)')
    min_rental_soc = fields.Float('SOC tối thiểu (%)', default=70)
    maintenance_plan_ids = fields.One2many(
        'motorbike.maintenance.plan', 'vehicle_id', string='Kế hoạch bảo dưỡng')
    next_service_date = fields.Date('Ngày bảo dưỡng tiếp theo')
    next_service_odo = fields.Float('ODO bảo dưỡng tiếp theo')

    @api.depends('battery_assignment_ids.battery_id', 'battery_assignment_ids.removed_at')
    def _compute_current_battery(self):
        for vehicle in self:
            current = vehicle.battery_assignment_ids.filtered(lambda item: not item.removed_at)
            vehicle.current_battery_id = current[:1].battery_id

    @api.constrains('min_rental_soc', 'next_service_odo')
    def _check_fleet_values(self):
        for vehicle in self:
            if not 0 <= vehicle.min_rental_soc <= 100 or vehicle.next_service_odo < 0:
                raise ValidationError(_('SOC phải từ 0–100%; ODO bảo dưỡng không được âm.'))

    # Legacy Week 5 fields retained for upgrade safety, hidden from the V2 UI.
    # Battery master data is now owned by motorbike.battery.
    battery_serial = fields.Char('Số sê-ri pin', copy=False, tracking=True)
    battery_capacity_kwh = fields.Float('Dung lượng pin (kWh)', tracking=True)
    battery_voltage = fields.Float('Điện áp pin (V)')
    battery_health = fields.Float('Sức khỏe pin (%)', default=100, tracking=True)
    charging_time_hours = fields.Float('Thời gian sạc đầy (giờ)')
    battery_warranty_until = fields.Date('Hạn bảo hành pin')

    @api.constrains('battery_capacity_kwh', 'battery_voltage', 'battery_health', 'charging_time_hours')
    def _check_battery_values(self):
        for vehicle in self:
            if min(vehicle.battery_capacity_kwh, vehicle.battery_voltage, vehicle.charging_time_hours) < 0:
                raise ValidationError(_('Thông số pin và thời gian sạc không được âm.'))
            if not 0 <= vehicle.battery_health <= 100:
                raise ValidationError(_('Sức khỏe pin phải nằm trong khoảng 0–100%.'))

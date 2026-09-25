from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_electric_motorbike = fields.Boolean('Xe máy điện', tracking=True)
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

from odoo import fields, models


class FleetVehicleOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    source_type = fields.Selection([
        ('manual', 'Nhập tay'), ('delivery', 'Giao xe'),
        ('return', 'Trả xe'), ('maintenance', 'Bảo dưỡng'),
    ], default='manual', required=True, string='Nguồn')
    service_id = fields.Many2one('fleet.vehicle.log.services', string='Hồ sơ bảo dưỡng', ondelete='set null')
    note = fields.Text('Ghi chú')

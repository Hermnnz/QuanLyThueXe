from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    is_electric_motorbike = fields.Boolean(related='vehicle_id.is_electric_motorbike')
    maintenance_component = fields.Selection([
        ('general', 'Tổng quát'), ('battery', 'Pin'), ('motor', 'Động cơ'),
        ('brakes', 'Phanh'), ('tires', 'Lốp'), ('charger', 'Bộ sạc'),
    ], string='Hạng mục bảo dưỡng', default='general', required=True)
    technician_id = fields.Many2one('res.partner', string='Kỹ thuật viên')
    maintenance_result = fields.Text('Kết quả / công việc đã thực hiện')
    next_maintenance_date = fields.Date('Ngày bảo dưỡng tiếp theo')

    @api.constrains('date', 'next_maintenance_date')
    def _check_next_maintenance_date(self):
        for service in self:
            if service.date and service.next_maintenance_date and service.next_maintenance_date < service.date:
                raise ValidationError(_('Ngày bảo dưỡng tiếp theo không được trước ngày thực hiện.'))

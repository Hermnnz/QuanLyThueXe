import math

from odoo import api, models
from odoo.exceptions import ValidationError


class FleetVehicleOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    @api.constrains('value', 'date', 'vehicle_id')
    def _check_motorbike_odometer(self):
        for log in self.filtered(lambda r: r.vehicle_id.is_electric_motorbike):
            if not math.isfinite(log.value):
                raise ValidationError('ODO phải là một số hữu hạn.')
            if log.value < 0:
                raise ValidationError('ODO không được âm.')
            if not log.date:
                raise ValidationError('Cần ngày ghi nhận ODO.')
            others = self.sudo().search([('vehicle_id', '=', log.vehicle_id.id), ('id', '!=', log.id)])
            if any((other.date < log.date and other.value > log.value) or
                   (other.date > log.date and other.value < log.value)
                   for other in others if other.date):
                raise ValidationError('ODO phải không giảm theo ngày ghi nhận.')

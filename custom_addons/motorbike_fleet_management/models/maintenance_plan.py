from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MotorbikeMaintenancePlan(models.Model):
    _name = 'motorbike.maintenance.plan'
    _description = 'Kế hoạch bảo dưỡng định kỳ'

    name = fields.Char('Tên kế hoạch', required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Xe', required=True, ondelete='cascade')
    service_type_id = fields.Many2one('fleet.service.type', string='Loại dịch vụ')
    interval_km = fields.Float('Chu kỳ (km)')
    interval_days = fields.Integer('Chu kỳ (ngày)')
    last_service_odo = fields.Float('ODO lần trước')
    last_service_date = fields.Date('Ngày lần trước')
    next_service_odo = fields.Float('ODO tiếp theo')
    next_service_date = fields.Date('Ngày tiếp theo')
    warning_km = fields.Float('Cảnh báo trước (km)')
    warning_days = fields.Integer('Cảnh báo trước (ngày)')
    active = fields.Boolean(default=True)

    @api.constrains('interval_km', 'interval_days', 'last_service_odo', 'next_service_odo', 'warning_km', 'warning_days')
    def _check_values(self):
        for plan in self:
            if min(plan.interval_km, plan.interval_days, plan.last_service_odo,
                   plan.next_service_odo, plan.warning_km, plan.warning_days) < 0:
                raise ValidationError(_('Chu kỳ, ODO và mức cảnh báo không được âm.'))

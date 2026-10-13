from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RentalVehicleType(models.Model):
    _name = 'rental.vehicle.type'
    _description = 'Dòng xe và bảng giá thuê'
    _order = 'name'

    name = fields.Char(string='Tên dòng xe', required=True)
    model_id = fields.Many2one(
        'fleet.vehicle.model',
        string='Dòng xe',
        required=True,
        ondelete='restrict',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        required=True,
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )
    daily_rate = fields.Monetary(string='Giá thuê mỗi ngày', required=True, default=0)
    active = fields.Boolean(string='Đang hoạt động', default=True)

    @api.constrains('daily_rate')
    def _check_daily_rate(self):
        if any(vehicle_type.daily_rate < 0 for vehicle_type in self):
            raise ValidationError(_('Giá thuê mỗi ngày không được âm.'))
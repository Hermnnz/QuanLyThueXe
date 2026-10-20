from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RentalVehicleType(models.Model):
    _name = 'rental.vehicle.type'
    _description = 'Dòng xe và bảng giá thuê'
    _order = 'name'
    _sql_constraints = [
        (
            'nonnegative_rental_daily_rate',
            'CHECK(daily_rate >= 0)',
            'Giá thuê mỗi ngày không được âm.',
        ),
    ]

    name = fields.Char(string='Tên dòng xe', required=True)
    model_id = fields.Many2one(
        'fleet.vehicle.model',
        string='Dòng xe',
        required=True,
        ondelete='restrict',
        domain=[('vehicle_type', '=', 'bike')],
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

    @api.constrains('model_id')
    def _check_motorbike_model(self):
        for vehicle_type in self:
            if vehicle_type.model_id.vehicle_type != 'bike':
                raise ValidationError(_('Chỉ được lập bảng giá cho dòng xe máy.'))

    @api.constrains('daily_rate')
    def _check_daily_rate(self):
        if any(vehicle_type.daily_rate < 0 for vehicle_type in self):
            raise ValidationError(_('Giá thuê mỗi ngày không được âm.'))
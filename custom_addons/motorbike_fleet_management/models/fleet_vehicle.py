from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    # Week 6: fields are entered and edited manually through List/Form.
    is_electric_motorbike = fields.Boolean('Xe máy điện', tracking=True)
    vehicle_code = fields.Char('Mã xe', copy=False, index=True)
    operational_status = fields.Selection([
        ('available', 'Sẵn sàng'), ('rented', 'Đang thuê'),
        ('inspection', 'Chờ kiểm tra'), ('maintenance', 'Bảo dưỡng'),
    ], default='inspection', required=True, copy=False, string='Trạng thái vận hành', tracking=True)
    technical_ready = fields.Boolean('Đạt điều kiện kỹ thuật', default=False, copy=False, tracking=True)
    rental_blocked = fields.Boolean('Khóa thuê', tracking=True)
    block_reason = fields.Text('Lý do khóa')
    next_service_date = fields.Date('Ngày bảo dưỡng tiếp theo')

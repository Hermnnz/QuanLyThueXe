from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_electric_motorbike = fields.Boolean('Xe máy điện', tracking=True)
    vehicle_code = fields.Char('Mã xe', copy=False, index=True)
    operational_status = fields.Selection([
        ('available', 'Sẵn sàng'), ('rented', 'Đang thuê'),
        ('inspection', 'Chờ kiểm tra'), ('maintenance', 'Bảo dưỡng'),
    ], default='inspection', required=True, copy=False, group_expand=True,
       string='Trạng thái vận hành', tracking=True)
    technical_ready = fields.Boolean('Đạt điều kiện kỹ thuật', default=False, copy=False, tracking=True)
    rental_blocked = fields.Boolean('Khóa thuê', tracking=True)
    block_reason = fields.Text('Lý do khóa')
    next_service_date = fields.Date('Ngày bảo dưỡng tiếp theo')

    def _running_blocking_services(self):
        # Check all records after access to the vehicle has been checked by the caller.
        return self.env['fleet.vehicle.log.services'].sudo().search([
            ('vehicle_id', 'in', self.ids), ('state', '=', 'running'),
            ('blocks_rental', '=', True), ('active', '=', True)])

    @api.constrains('is_electric_motorbike', 'operational_status', 'technical_ready',
                    'rental_blocked', 'block_reason', 'active')
    def _check_rental_condition(self):
        for vehicle in self.filtered('is_electric_motorbike'):
            if vehicle.rental_blocked and not (vehicle.block_reason or '').strip():
                raise ValidationError('Cần nhập lý do khi khóa thuê xe.')
            if vehicle.operational_status == 'available' and not vehicle.technical_ready:
                raise ValidationError('Xe sẵn sàng phải đạt điều kiện kỹ thuật.')
            if vehicle._running_blocking_services() and (
                    vehicle.operational_status != 'maintenance' or vehicle.technical_ready):
                raise ValidationError('Xe đang bảo dưỡng chặn thuê phải ở trạng thái bảo dưỡng và chưa đạt kỹ thuật.')

    def action_confirm_technical_ready(self):
        self.check_access('write')
        for vehicle in self:
            if not vehicle.is_electric_motorbike or not vehicle.active:
                raise UserError('Chỉ xác nhận kỹ thuật cho xe điện đang khai thác.')
            if vehicle.operational_status == 'rented':
                raise UserError('Không xác nhận sẵn sàng khi xe đang được thuê.')
            if vehicle._running_blocking_services():
                raise UserError('Còn bảo dưỡng đang thực hiện và chặn thuê.')
        return self.write({'technical_ready': True, 'operational_status': 'available'})

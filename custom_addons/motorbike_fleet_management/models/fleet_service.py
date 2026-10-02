from odoo import fields, models


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    # Week 6: records, status and dates are editable; no business workflow yet.
    is_electric_motorbike = fields.Boolean(related='vehicle_id.is_electric_motorbike')
    service_type_id = fields.Many2one(default=lambda self: self.env.ref(
        'motorbike_fleet_management.service_type_electric_maintenance', raise_if_not_found=False))
    technician_id = fields.Many2one('res.partner', string='Kỹ thuật viên')
    result = fields.Text('Kết quả / công việc đã thực hiện')
    next_service_date = fields.Date('Ngày bảo dưỡng tiếp theo')
    maintenance_type = fields.Selection([
        ('preventive', 'Định kỳ'), ('corrective', 'Sửa chữa'), ('emergency', 'Khẩn cấp'),
    ], default='preventive', required=True, string='Loại bảo dưỡng')
    scheduled_start = fields.Datetime('Dự kiến bắt đầu')
    scheduled_end = fields.Datetime('Dự kiến kết thúc')
    actual_start = fields.Datetime('Thực tế bắt đầu', copy=False)
    actual_end = fields.Datetime('Thực tế kết thúc', copy=False)
    blocks_rental = fields.Boolean('Ghi nhận chặn thuê', default=True)
    cost = fields.Monetary(related='amount', readonly=False, string='Chi phí')
    state = fields.Selection(selection_add=[('scheduled', 'Đã lên lịch'), ('running',)],
                             ondelete={'scheduled': 'set default'}, copy=False)

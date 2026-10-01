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
    maintenance_type = fields.Selection([
        ('preventive', 'Định kỳ'), ('corrective', 'Sửa chữa'),
        ('emergency', 'Khẩn cấp'), ('battery', 'Pin'),
    ], default='preventive', required=True, string='Loại bảo dưỡng')
    scheduled_start = fields.Datetime('Dự kiến bắt đầu')
    scheduled_end = fields.Datetime('Dự kiến kết thúc')
    actual_start = fields.Datetime('Thực tế bắt đầu')
    actual_end = fields.Datetime('Thực tế kết thúc')
    blocks_rental = fields.Boolean('Khóa lịch thuê', default=True)
    cost = fields.Monetary(related='amount', readonly=False, string='Chi phí')
    result = fields.Text(related='maintenance_result', readonly=False, string='Kết quả')
    # Preserve Fleet's native state keys for its views and reports.
    state = fields.Selection(selection_add=[('scheduled', 'Đã lên lịch'), ('running',)],
                             ondelete={'scheduled': 'set default'})

    @api.constrains('scheduled_start', 'scheduled_end', 'actual_start', 'actual_end')
    def _check_periods(self):
        for service in self:
            for start, end in [(service.scheduled_start, service.scheduled_end),
                               (service.actual_start, service.actual_end)]:
                if start and end and end < start:
                    raise ValidationError(_('Thời gian kết thúc không được trước thời gian bắt đầu.'))

    @api.constrains('date', 'next_maintenance_date')
    def _check_next_maintenance_date(self):
        for service in self:
            if service.date and service.next_maintenance_date and service.next_maintenance_date < service.date:
                raise ValidationError(_('Ngày bảo dưỡng tiếp theo không được trước ngày thực hiện.'))

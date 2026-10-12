from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

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

    @api.constrains('vehicle_id', 'scheduled_start', 'scheduled_end', 'actual_start',
                    'actual_end', 'amount', 'next_service_date', 'date', 'state')
    def _check_maintenance_values(self):
        for service in self.filtered('is_electric_motorbike'):
            if service.amount < 0:
                raise ValidationError('Chi phí bảo dưỡng không được âm.')
            for start, end in [(service.scheduled_start, service.scheduled_end),
                               (service.actual_start, service.actual_end)]:
                if end and not start:
                    raise ValidationError('Cần nhập thời gian bắt đầu trước thời gian kết thúc.')
                if start and end and end < start:
                    raise ValidationError('Thời gian kết thúc không được trước thời gian bắt đầu.')
            if service.state == 'scheduled' and not (service.scheduled_start and service.scheduled_end):
                raise ValidationError('Lên lịch bảo dưỡng cần đủ thời gian dự kiến bắt đầu và kết thúc.')
            if service.next_service_date and service.date and service.next_service_date <= service.date:
                raise ValidationError('Mốc bảo dưỡng tiếp theo phải sau ngày hồ sơ bảo dưỡng.')

    def _check_start_vehicle(self):
        for service in self.filtered('is_electric_motorbike'):
            vehicle = service.vehicle_id
            if not service.active or not vehicle.active:
                raise UserError('Không bắt đầu bảo dưỡng cho hồ sơ hoặc xe đã lưu trữ.')
            if service.blocks_rental:
                vehicle.check_access('write')
            if service.blocks_rental and vehicle.operational_status == 'renting':
                raise UserError('Xe đang được thuê; chưa thể bắt đầu bảo dưỡng chặn thuê.')

    def _start_vehicle_maintenance(self):
        for vehicle in self.filtered(lambda s: s.is_electric_motorbike and s.blocks_rental).vehicle_id:
            vehicle.write({'operational_status': 'maintenance', 'technical_ready': False})

    def _release_vehicle_maintenance(self):
        for vehicle in self.filtered(lambda s: s.is_electric_motorbike and s.blocks_rental).vehicle_id:
            if not vehicle._running_blocking_services() and vehicle.operational_status == 'maintenance':
                vehicle.write({'operational_status': 'pending_inspection', 'technical_ready': False})

    @api.model_create_multi
    def create(self, vals_list):
        # Completed historical records may be imported; they do not change today's vehicle state.
        services = super().create(vals_list)
        running = services.filtered(lambda s: s.is_electric_motorbike and s.state == 'running')
        running._check_start_vehicle()
        for service in running:
            if not service.actual_start:
                service.write({'actual_start': fields.Datetime.now()})
        running._start_vehicle_maintenance()
        return services

    def write(self, vals):
        self.check_access('write')
        target = self.env['fleet.vehicle'].browse(vals.get('vehicle_id'))
        electric = self.filtered(lambda s: s.is_electric_motorbike or target.is_electric_motorbike)
        running = electric.filtered(lambda s: s.state == 'running')
        if running and any(key in vals for key in ('vehicle_id', 'blocks_rental', 'active')):
            raise UserError('Hoàn tất hoặc hủy bảo dưỡng đang chạy trước khi đổi xe, chặn thuê hoặc lưu trữ.')
        if 'vehicle_id' in vals and electric.filtered(lambda s: s.state in ('done', 'cancelled')):
            raise UserError('Không đổi xe của hồ sơ bảo dưỡng đã kết thúc.')
        transitions = {'new': {'scheduled', 'running', 'cancelled'},
                       'scheduled': {'running', 'cancelled'}, 'running': {'done', 'cancelled'},
                       'done': set(), 'cancelled': set()}
        changed = electric.filtered(lambda s: 'state' in vals and s.state != vals['state'])
        for service in changed:
            if vals['state'] not in transitions[service.state]:
                raise UserError('Chuyển trạng thái bảo dưỡng không hợp lệ.')
        starting = changed if vals.get('state') == 'running' else self.browse()
        ending = changed.filtered(lambda s: s.state == 'running') if vals.get('state') in ('done', 'cancelled') else self.browse()
        starting._check_start_vehicle()
        for service in changed:
            if vals.get('state') == 'done' and not (vals.get('result', service.result) or '').strip():
                raise UserError('Nhập kết quả công việc trước khi hoàn tất bảo dưỡng.')
        # Process individually so existing historical timestamps are preserved.
        if changed:
            for service in self:
                values = dict(vals)
                if service in starting and not values.get('actual_start', service.actual_start):
                    values['actual_start'] = fields.Datetime.now()
                if service in ending and not values.get('actual_end', service.actual_end):
                    values['actual_end'] = fields.Datetime.now()
                super(FleetVehicleLogServices, service).write(values)
        else:
            super().write(vals)
        # Recheck the final vehicle if it was changed in the same write.
        starting._check_start_vehicle()
        starting._start_vehicle_maintenance()
        ending._release_vehicle_maintenance()
        for service in changed.filtered(lambda s: s.state == 'done' and s.next_service_date):
            vehicle = service.vehicle_id
            vehicle.check_access('write')
            latest = self.search([('vehicle_id', '=', vehicle.id), ('state', '=', 'done'),
                                  ('next_service_date', '!=', False)], order='date desc, id desc', limit=1)
            if latest == service:
                vehicle.next_service_date = service.next_service_date
        return True

    def unlink(self):
        if self.filtered(lambda s: s.is_electric_motorbike and s.state == 'running'):
            raise UserError('Không xóa bảo dưỡng đang thực hiện; hãy hoàn tất hoặc hủy trước.')
        return super().unlink()

    def action_schedule(self):
        return self.write({'state': 'scheduled'})

    def action_start(self):
        return self.write({'state': 'running'})

    def action_done(self):
        return self.write({'state': 'done'})

    def action_cancel(self):
        return self.write({'state': 'cancelled'})

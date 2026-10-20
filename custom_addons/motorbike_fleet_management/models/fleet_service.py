import math

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    is_electric_motorbike = fields.Boolean(related='vehicle_id.is_electric_motorbike')
    vehicle_code = fields.Char(related='vehicle_id.vehicle_code', string='Mã phương tiện', readonly=True)
    customer_name = fields.Char(string='Khách hàng')
    customer_phone = fields.Char(string='Số điện thoại khách hàng')
    service_type_id = fields.Many2one(default=lambda self: self.env.ref(
        'motorbike_fleet_management.service_type_electric_maintenance', raise_if_not_found=False))
    technician_id = fields.Many2one('res.partner', string='Kỹ thuật viên')
    result = fields.Text('Kết quả / công việc đã thực hiện', copy=False)
    next_service_date = fields.Date('Ngày bảo dưỡng tiếp theo')
    maintenance_type = fields.Selection([
        ('preventive', 'Định kỳ'), ('corrective', 'Sửa chữa'), ('emergency', 'Khẩn cấp'),
    ], default='preventive', required=True, string='Loại bảo dưỡng')
    actual_start = fields.Datetime('Ngày bắt đầu', copy=False)
    actual_end = fields.Datetime('Ngày kết thúc', copy=False)
    blocks_rental = fields.Boolean('Ghi nhận chặn thuê', default=True)
    cost = fields.Monetary(related='amount', readonly=False, string='Chi phí')
    state = fields.Selection(copy=False)

    @api.constrains('vehicle_id', 'actual_start',
                    'actual_end', 'amount', 'next_service_date', 'date', 'state', 'blocks_rental')
    def _check_maintenance_values(self):
        for service in self.filtered('is_electric_motorbike'):
            if not math.isfinite(service.amount) or service.amount < 0:
                raise ValidationError('Chi phí bảo dưỡng phải là số hữu hạn, không âm.')
            for start, end in [(service.actual_start, service.actual_end)]:
                if end and not start:
                    raise ValidationError('Cần nhập thời gian bắt đầu trước thời gian kết thúc.')
                if start and end and end < start:
                    raise ValidationError('Thời gian kết thúc không được trước thời gian bắt đầu.')
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
                finished = self.filtered(lambda s: s.vehicle_id == vehicle)
                passed = bool(finished) and all(s.state == 'done' for s in finished)
                vehicle._write_operational_state({
                    'operational_status': 'available' if passed else 'pending_inspection',
                    'technical_ready': passed})

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if 'customer_id' in values and not values.get('customer_name'):
                cid = values.get('customer_id')
                if isinstance(cid, int):
                    partner = self.env['res.partner'].browse(cid)
                    values['customer_name'] = partner.name
                    if not values.get('customer_phone') and (partner.phone or partner.mobile):
                        values['customer_phone'] = partner.phone or partner.mobile
                elif isinstance(cid, str):
                    values['customer_name'] = cid
            vehicle = self.env['fleet.vehicle'].browse(
                values.get('vehicle_id') or self.env.context.get('default_vehicle_id'))
            if vehicle.is_electric_motorbike:
                if values.get('state', self.env.context.get('default_state')) == 'done':
                    if not self.env.user.has_group('fleet.fleet_group_manager'):
                        raise UserError('Chỉ quản trị Fleet được nhập hồ sơ lịch sử đã hoàn tất.')
                    if not ((values.get('result') or '').strip()
                            and values.get('actual_start') and values.get('actual_end')):
                        raise ValidationError('Hồ sơ lịch sử hoàn tất cần kết quả và đủ thời gian thực tế.')
                costs = {key: self.env.context['default_' + key]
                         for key in ('amount', 'cost') if 'default_' + key in self.env.context}
                costs.update(values)
                self._validate_cost_input(costs)
        # Completed historical records may be imported; they do not change today's vehicle state.
        services = super().create(vals_list)
        running = services.filtered(lambda s: s.is_electric_motorbike and s.state == 'running')
        running._check_start_vehicle()
        for service in running:
            if not service.actual_start:
                service.write({'actual_start': fields.Datetime.now()})
        running._start_vehicle_maintenance()
        return services

    @api.model
    def _validate_cost_input(self, values):
        # Monetary fields round before ORM constraints run. Reject invalid input
        # here so import/RPC returns a business error rather than a rounding crash.
        for key in ('amount', 'cost'):
            if key not in values:
                continue
            try:
                value = float(values[key] or 0)
            except (TypeError, ValueError, OverflowError):
                raise ValidationError('Chi phí bảo dưỡng phải là số hữu hạn, không âm.')
            if values[key] is True or not math.isfinite(value) or value < 0:
                raise ValidationError('Chi phí bảo dưỡng phải là số hữu hạn, không âm.')

    def write(self, vals):
        self.check_access('write')
        if 'customer_id' in vals and not vals.get('customer_name'):
            cid = vals.get('customer_id')
            if isinstance(cid, int):
                partner = self.env['res.partner'].browse(cid)
                vals['customer_name'] = partner.name
                if not vals.get('customer_phone') and (partner.phone or partner.mobile):
                    vals['customer_phone'] = partner.phone or partner.mobile
            elif isinstance(cid, str):
                vals['customer_name'] = cid
        target = self.env['fleet.vehicle'].browse(vals.get('vehicle_id'))
        electric = self.filtered(lambda s: s.is_electric_motorbike or target.is_electric_motorbike)
        if electric:
            self._validate_cost_input(vals)
        protected = {'vehicle_id', 'description', 'date', 'amount', 'cost', 'result',
                     'maintenance_type', 'next_service_date', 'blocks_rental',
                     'actual_start', 'actual_end'}
        for service in electric.filtered(lambda s: s.state in ('done', 'cancelled')):
            if any(key in vals and vals[key] != service[key] for key in protected):
                raise UserError('Hồ sơ đã kết thúc không được sửa nội dung nghiệp vụ; dùng ghi chú để bổ sung thông tin.')
        running = electric.filtered(lambda s: s.state == 'running')
        if running and any(key in vals for key in ('vehicle_id', 'blocks_rental', 'active')):
            raise UserError('Hoàn tất hoặc hủy bảo dưỡng đang chạy trước khi đổi xe, chặn thuê hoặc lưu trữ.')
        if 'vehicle_id' in vals and electric.filtered(lambda s: s.state in ('done', 'cancelled')):
            raise UserError('Không đổi xe của hồ sơ bảo dưỡng đã kết thúc.')
        transitions = {'new': {'running', 'cancelled'}, 'running': {'done', 'cancelled'},
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
            latest = self.with_context(active_test=False).search([('vehicle_id', '=', vehicle.id), ('state', '=', 'done'),
                                  ('next_service_date', '!=', False)], order='date desc, id desc', limit=1)
            if latest == service:
                vehicle.next_service_date = service.next_service_date
        return True

    def unlink(self):
        if self.filtered(lambda s: s.is_electric_motorbike and s.state == 'running'):
            raise UserError('Không xóa bảo dưỡng đang thực hiện; hãy hoàn tất hoặc hủy trước.')
        milestones = {service.vehicle_id.id: service.vehicle_id.next_service_date
                      for service in self.filtered(lambda s: s.is_electric_motorbike
                          and s.state == 'done' and s.next_service_date
                          and s.vehicle_id.next_service_date == s.next_service_date)}
        vehicles = self.env['fleet.vehicle'].browse(list(milestones))
        vehicles.check_access('write')
        result = super().unlink()
        for vehicle in vehicles:
            latest = self.with_context(active_test=False).search([
                ('vehicle_id', '=', vehicle.id), ('state', '=', 'done'),
                ('next_service_date', '!=', False)], order='date desc, id desc', limit=1)
            vehicle.next_service_date = latest.next_service_date if latest else False
        return result

    def action_start(self):
        return self.write({'state': 'running'})

    def action_done(self):
        return self.write({'state': 'done'})

    def action_cancel(self):
        return self.write({'state': 'cancelled'})

import math
import re

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    service_code = fields.Char(
        string='Mã phiếu', copy=False, index=True,
        default=lambda self: self._find_next_available_code(),
    )
    service_code_key = fields.Char(
        compute='_compute_service_code_key', store=True, copy=False, index=True,
    )

    if hasattr(models, 'Constraint'):
        _service_code_unique = models.Constraint('UNIQUE(service_code)', 'Mã phiếu bảo dưỡng đã tồn tại.')
        _normalized_service_code_unique = models.Constraint(
            'UNIQUE(service_code_key)',
            'Mã phiếu bảo dưỡng đã tồn tại (không phân biệt hoa thường/khoảng trắng).'
        )
    else:
        _sql_constraints = [
            ('service_code_unique', 'UNIQUE(service_code)', 'Mã phiếu bảo dưỡng đã tồn tại.'),
            ('normalized_service_code_unique', 'UNIQUE(service_code_key)',
             'Mã phiếu bảo dưỡng đã tồn tại (không phân biệt hoa thường/khoảng trắng).'),
        ]

    is_electric_motorbike = fields.Boolean(related='vehicle_id.is_electric_motorbike')
    vehicle_code = fields.Char(related='vehicle_id.vehicle_code', string='Mã phương tiện', readonly=True)
    customer_name = fields.Char(string='Khách hàng')
    customer_phone = fields.Char(string='Số điện thoại khách hàng')
    service_type_id = fields.Many2one(default=lambda self: self.env.ref(
        'motorbike_fleet_management.service_type_electric_maintenance', raise_if_not_found=False))

    def _domain_technician_id(self):
        tech_group = self.env.ref('motorbike_fleet_management.group_motorbike_technician', raise_if_not_found=False)
        manager_group = self.env.ref('motorbike_fleet_management.group_fleet_manager', raise_if_not_found=False)
        if not tech_group:
            return []
        domain = [('user_ids.groups_id', 'in', [tech_group.id])]
        if manager_group:
            domain.append(('user_ids.groups_id', 'not in', [manager_group.id]))
        return domain

    technician_id = fields.Many2one(
        'res.partner',
        string='Kỹ thuật viên',
        domain=_domain_technician_id,
    )
    is_fleet_manager = fields.Boolean(compute='_compute_is_fleet_manager')

    def _compute_is_fleet_manager(self):
        user = self.env.user
        is_mgr = bool(user.has_group('motorbike_fleet_management.group_fleet_manager') or user.has_group('base.group_system'))
        for record in self:
            record.is_fleet_manager = is_mgr

    can_claim_ticket = fields.Boolean(compute='_compute_can_claim_ticket')

    def _compute_can_claim_ticket(self):
        user = self.env.user
        is_tech = user.has_group('motorbike_fleet_management.group_motorbike_technician')
        is_manager = user.has_group('motorbike_fleet_management.group_fleet_manager') or user.has_group('base.group_system')
        can_claim = bool(is_tech and not is_manager)
        for record in self:
            record.can_claim_ticket = bool(can_claim and record.state == 'new' and record.is_electric_motorbike)

    result = fields.Text('Kết quả / công việc đã thực hiện', copy=False)
    next_service_date = fields.Date('Ngày bảo dưỡng tiếp theo')
    maintenance_type = fields.Selection([
        ('preventive', 'Định kỳ'), ('corrective', 'Sửa chữa'), ('emergency', 'Khẩn cấp'),
    ], default='preventive', required=True, string='Loại bảo dưỡng')
    actual_start = fields.Datetime('Ngày bắt đầu', copy=False)
    actual_end = fields.Datetime('Ngày kết thúc', copy=False)
    blocks_rental = fields.Boolean('Tạm khóa xe khi bảo dưỡng', default=True)
    cost = fields.Monetary(related='amount', readonly=False, string='Chi phí')
    state = fields.Selection([
        ('new', 'Mới'),
        ('running', 'Đang thực hiện'),
        ('done', 'Hoàn tất'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', copy=False)

    @api.model
    def _clean_code(cls, val):
        if not val:
            return False
        return re.sub(r'\s+', '', str(val)).upper()

    @api.depends('service_code')
    def _compute_service_code_key(self):
        for service in self:
            service.service_code_key = self._clean_code(service.service_code) or False

    @api.model
    def _find_next_available_code(self, reserved_codes=None):
        reserved = set(reserved_codes or [])
        records = self.sudo().with_context(active_test=False).search_read(
            [('service_code', '=like', 'BD%')], ['service_code']
        )
        used_nums = set()
        for rec in records:
            val = (rec.get('service_code') or '').strip().upper()
            if val.startswith('BD') and val[2:].isdigit():
                try:
                    used_nums.add(int(val[2:]))
                except ValueError:
                    pass
        for val in reserved:
            val = (val or '').strip().upper()
            if val.startswith('BD') and val[2:].isdigit():
                try:
                    used_nums.add(int(val[2:]))
                except ValueError:
                    pass
        candidate = 1
        while candidate in used_nums:
            candidate += 1
        return f"BD{candidate:05d}"

    @api.depends('service_code', 'service_type_id', 'vehicle_id.name')
    def _compute_display_name(self):
        super()._compute_display_name()
        for service in self:
            if service.service_code:
                type_name = service.service_type_id.name or 'Bảo dưỡng'
                vehicle_name = f" - {service.vehicle_id.name}" if service.vehicle_id else ""
                service.display_name = f"[{service.service_code}] {type_name}{vehicle_name}"

    @api.constrains('vehicle_id', 'actual_start',
                    'actual_end', 'amount', 'next_service_date', 'date', 'state', 'blocks_rental')
    def _check_maintenance_values(self):
        for service in self.filtered('is_electric_motorbike'):
            if not math.isfinite(service.amount) or service.amount < 0:
                raise ValidationError('Chi phí bảo dưỡng phải là số hữu hạn, không âm.')
            if service.actual_end and not service.actual_start:
                raise ValidationError('Cần nhập thời gian bắt đầu trước thời gian kết thúc.')
            if service.actual_start and service.actual_end and service.actual_end < service.actual_start:
                raise ValidationError('Thời gian kết thúc không được trước thời gian bắt đầu.')
            if service.next_service_date and service.date and service.next_service_date <= service.date:
                raise ValidationError('Mốc bảo dưỡng tiếp theo phải sau ngày hồ sơ bảo dưỡng.')

    @api.constrains('technician_id')
    def _check_technician_id(self):
        manager_group = self.env.ref('motorbike_fleet_management.group_fleet_manager', raise_if_not_found=False)
        for service in self.filtered('technician_id'):
            if manager_group and manager_group in service.technician_id.user_ids.groups_id:
                raise ValidationError('Không được phân công Quản lý/Admin làm kỹ thuật viên sửa chữa.')

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
            vals = {'operational_status': 'maintenance', 'technical_ready': False}
            if vehicle.operational_status != 'maintenance':
                vals['pre_maintenance_status'] = vehicle.operational_status
            vehicle._write_operational_state(vals)

    def _release_vehicle_maintenance(self):
        for vehicle in self.filtered(lambda s: s.is_electric_motorbike and s.blocks_rental).vehicle_id:
            if not vehicle._running_blocking_services() and vehicle.operational_status == 'maintenance':
                finished = self.filtered(lambda s: s.vehicle_id == vehicle)
                # Xe chỉ trở về Sẵn sàng nếu trước khi bảo dưỡng xe đã sẵn sàng và tất cả phiếu đều hoàn tất (passed)
                ready = bool(finished) and all(s.state == 'done' for s in finished) and vehicle.pre_maintenance_status == 'available'
                vehicle._write_operational_state({
                    'operational_status': 'available' if ready else 'pending_inspection',
                    'technical_ready': ready,
                    'pre_maintenance_status': False})

    # Helper nội bộ bóc tách customer_id từ giao diện/bên ngoài để tự động điền tên và số điện thoại
    def _pop_customer_vals(self, values):
        customer_id = values.pop('customer_id', None)
        if customer_id and not values.get('customer_name'):
            if isinstance(customer_id, int):
                partner = self.env['res.partner'].browse(customer_id)
                values['customer_name'] = partner.name
                if not values.get('customer_phone') and (partner.phone or partner.mobile):
                    values['customer_phone'] = partner.phone or partner.mobile
            elif isinstance(customer_id, str):
                values['customer_name'] = customer_id

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        reserved_in_batch = set()
        for values in vals_list:
            values = dict(values)
            self._pop_customer_vals(values)
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

            # Auto-assign service_code if not set or colliding
            code = self._clean_code(values.get('service_code'))
            if not code:
                code = self._find_next_available_code(reserved_codes=reserved_in_batch)
            elif code.startswith('BD') and (self.sudo().with_context(active_test=False).search_count([('service_code_key', '=', code)]) or code in reserved_in_batch):
                code = self._find_next_available_code(reserved_codes=reserved_in_batch)
            reserved_in_batch.add(code)
            values['service_code'] = code
            prepared.append(values)

        # Completed historical records may be imported; they do not change today's vehicle state.
        services = super().create(prepared)
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
        for key in {'amount', 'cost'} & set(values):
            try:
                value = float(values[key] or 0)
            except (TypeError, ValueError, OverflowError):
                raise ValidationError('Chi phí bảo dưỡng phải là số hữu hạn, không âm.')
            if values[key] is True or not math.isfinite(value) or value < 0:
                raise ValidationError('Chi phí bảo dưỡng phải là số hữu hạn, không âm.')

    def write(self, vals):
        self.check_access('write')
        self._pop_customer_vals(vals)
        if 'technician_id' in vals and not self.env.context.get('is_claim_ticket_action'):
            user = self.env.user
            if not (user.has_group('motorbike_fleet_management.group_fleet_manager') or user.has_group('base.group_system')):
                raise UserError('Chỉ Quản lý xe mới có quyền phân công Kỹ thuật viên.')
        if 'service_code' in vals:
            cleaned = self._clean_code(vals['service_code'])
            if not cleaned:
                raise ValidationError('Không được xóa mã phiếu bảo dưỡng đã cấp.')
            vals['service_code'] = cleaned
        target = self.env['fleet.vehicle'].browse(vals.get('vehicle_id'))
        electric = self.filtered(lambda s: s.is_electric_motorbike or target.is_electric_motorbike)
        if electric:
            self._validate_cost_input(vals)
        for service in self:
            if service.state in ('done', 'cancelled') and set(vals) - {'notes', 'active'}:
                raise UserError('Hồ sơ đã kết thúc chỉ được bổ sung ghi chú.')
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
        for service in starting:
            tech = vals.get('technician_id', service.technician_id)
            if not tech:
                raise UserError('Vui lòng phân công Kỹ thuật viên phụ trách trước khi bắt đầu thực hiện.')
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
        # Tập rỗng không có hồ sơ nào để xóa; cho phép Odoo tiếp tục xử lý hóa đơn.
        if not self:
            return True
        # Giữ hồ sơ bảo dưỡng ở mọi trạng thái để bảo toàn lịch sử.
        raise UserError('Không được xóa hồ sơ bảo dưỡng; hãy hủy hoặc lưu trữ nếu cần.')

    def action_claim_ticket(self):
        user = self.env.user
        if user.has_group('motorbike_fleet_management.group_fleet_manager') or user.has_group('base.group_system'):
            raise UserError('Quản lý/Admin không nhận việc; thao tác này chỉ dành riêng cho Kỹ thuật viên.')
        if not user.has_group('motorbike_fleet_management.group_motorbike_technician'):
            raise UserError('Chỉ Kỹ thuật viên xe điện mới có quyền nhận việc.')
        for service in self:
            if service.state != 'new':
                raise UserError('Chỉ có thể nhận các phiếu đang ở trạng thái Mới.')
            service.with_context(is_claim_ticket_action=True).write({
                'technician_id': user.partner_id.id,
                'state': 'running',
            })
        return True

    def action_start(self):
        for service in self:
            if service.is_electric_motorbike and not service.technician_id:
                raise UserError('Vui lòng phân công Kỹ thuật viên phụ trách trước khi bắt đầu thực hiện.')
        return self.write({'state': 'running'})

    def action_done(self):
        return self.write({'state': 'done'})

    def action_cancel(self):
        return self.write({'state': 'cancelled'})

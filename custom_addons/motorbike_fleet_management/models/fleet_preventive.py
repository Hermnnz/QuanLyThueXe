"""Small periodic-maintenance policy on existing Fleet models."""
import math
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class FleetModelPreventive(models.Model):
    # Legacy storage only; no runtime policy inheritance.
    _inherit = 'fleet.vehicle.model'

    service_interval_km = fields.Float('Chu kỳ bảo dưỡng (km)', default=0)
    service_interval_months = fields.Integer('Chu kỳ bảo dưỡng (tháng)', default=0)
    service_warning_km = fields.Float('Báo trước (km)', default=200)
    service_warning_days = fields.Integer('Báo trước (ngày)', default=7)

    @api.constrains('service_interval_km', 'service_interval_months', 'service_warning_km', 'service_warning_days')
    def _check_service_policy(self):
        for model in self:
            for value in [model.service_interval_km, model.service_interval_months,
                          model.service_warning_km, model.service_warning_days]:
                if not math.isfinite(value) or value < 0:
                    raise ValidationError('Chu kỳ và ngưỡng cảnh báo phải là số hữu hạn, không âm.')
            if model.service_interval_km and model.service_warning_km >= model.service_interval_km:
                raise ValidationError('Ngưỡng báo trước km phải nhỏ hơn chu kỳ bảo dưỡng.')


class FleetVehiclePreventive(models.Model):
    _inherit = 'fleet.vehicle'

    service_reference_date = fields.Date('Ngày mốc ban đầu', tracking=True,
        help='Nhập mốc đã xác minh. Không tự suy đoán ngày bảo dưỡng của xe cũ.')
    service_reference_odo = fields.Float('ODO mốc ban đầu (km)', tracking=True)
    service_interval_km = fields.Float('Chu kỳ bảo dưỡng (km)', default=0, tracking=True)
    service_interval_months = fields.Integer('Chu kỳ bảo dưỡng (tháng)', default=0, tracking=True)
    service_warning_km = fields.Float('Báo trước (km)', default=200, tracking=True)
    service_warning_days = fields.Integer('Báo trước (ngày)', default=7, tracking=True)
    service_last_date = fields.Date('Mốc bảo dưỡng gần nhất', compute='_compute_service_schedule', store=True)
    service_last_odo = fields.Float('ODO tại mốc gần nhất', compute='_compute_service_schedule', store=True)
    service_next_date = fields.Date('Hạn định kỳ theo ngày', compute='_compute_service_schedule', store=True)
    service_next_odo = fields.Float('Hạn định kỳ theo ODO', compute='_compute_service_schedule', store=True)
    service_schedule_state = fields.Selection([
        ('unconfigured', 'Chưa cấu hình chu kỳ'), ('missing_baseline', 'Thiếu mốc ban đầu'),
        ('ok', 'Chưa đến hạn'), ('soon', 'Sắp đến hạn'), ('due', 'Đến hạn'), ('overdue', 'Quá hạn')],
        string='Hạn bảo dưỡng', compute='_compute_service_alert', store=True, index=True)
    service_alert_message = fields.Text('Chi tiết hạn bảo dưỡng', compute='_compute_service_alert', store=True)
    open_preventive_count = fields.Integer('Phiếu định kỳ đang xử lý', compute='_compute_open_preventive_count')

    @api.model_create_multi
    def create(self, vals_list):
        vehicles = super().create(vals_list)
        if not self.env.context.get('install_mode'):
            vehicles._auto_create_due_services()
        return vehicles

    def write(self, vals):
        result = super().write(vals)
        triggers = {'odometer', 'service_interval_km', 'service_interval_months',
                    'service_reference_date', 'service_reference_odo', 'active',
                    'is_electric_motorbike'}
        if triggers.intersection(vals) and not self.env.context.get('install_mode'):
            self._auto_create_due_services()
        return result

    def _auto_create_due_services(self):
        """Create a system draft only for a verified, due periodic milestone.

        The same vehicle lock is used by the manual button. Archived unfinished
        jobs also count, so hiding a job cannot silently create a duplicate.
        """
        services = self.env['fleet.vehicle.log.services'].sudo().with_context(active_test=False)
        created = services.browse()
        for vehicle in self.sudo().sorted('id'):
            self.env.cr.execute('SELECT id FROM fleet_vehicle WHERE id=%s FOR UPDATE', (vehicle.id,))
            vehicle.invalidate_recordset(['active', 'is_electric_motorbike', 'odometer',
                'service_interval_km', 'service_interval_months', 'service_last_date',
                'service_next_date', 'service_next_odo'])
            if not vehicle.active or not vehicle.is_electric_motorbike or not vehicle.service_last_date:
                continue
            due_km = bool(vehicle.service_interval_km and vehicle.odometer >= vehicle.service_next_odo)
            due_date = bool(vehicle.service_interval_months and vehicle.service_next_date
                            and vehicle.service_next_date <= vehicle._maintenance_today())
            if not (due_km or due_date):
                continue
            if services.search_count([('vehicle_id', '=', vehicle.id),
                    ('maintenance_type', '=', 'preventive'),
                    ('state', 'in', ['new', 'scheduled', 'running'])]):
                continue
            notes = ['Hệ thống tự tạo vì xe đến hoặc quá hạn bảo dưỡng định kỳ.']
            if due_km:
                notes.append('ODO hiện tại %g km; hạn %g km.' % (vehicle.odometer, vehicle.service_next_odo))
            if due_date:
                notes.append('Hạn theo ngày: %s.' % vehicle.service_next_date)
            created |= services.with_context(active_test=True).create({
                'vehicle_id': vehicle.id, 'maintenance_type': 'preventive', 'state': 'new',
                'company_id': vehicle.company_id.id or self.env.company.id,
                'description': 'Bảo dưỡng định kỳ tự động — ' + (vehicle.vehicle_code or vehicle.display_name),
                'notes': '\n'.join(notes), 'blocks_rental': True})
        return created

    @api.constrains('service_interval_km', 'service_interval_months', 'service_warning_km', 'service_warning_days')
    def _check_vehicle_service_policy(self):
        for vehicle in self:
            values = (vehicle.service_interval_km, vehicle.service_interval_months,
                      vehicle.service_warning_km, vehicle.service_warning_days)
            if any(not math.isfinite(value) or value < 0 for value in values):
                raise ValidationError('Chu kỳ và ngưỡng cảnh báo phải là số hữu hạn, không âm.')
            if vehicle.service_interval_km and vehicle.service_warning_km >= vehicle.service_interval_km:
                raise ValidationError('Ngưỡng báo trước km phải nhỏ hơn chu kỳ bảo dưỡng.')

    @api.constrains('service_reference_date', 'service_reference_odo', 'odometer')
    def _check_service_reference(self):
        for vehicle in self:
            if not math.isfinite(vehicle.service_reference_odo) or vehicle.service_reference_odo < 0:
                raise ValidationError('ODO mốc ban đầu phải hữu hạn và không âm.')
            if vehicle.service_reference_date and vehicle.service_reference_odo > vehicle.odometer:
                raise ValidationError('ODO mốc ban đầu không được lớn hơn ODO hiện tại.')
            if vehicle.service_reference_date and vehicle.service_reference_date > fields.Date.context_today(vehicle):
                raise ValidationError('Ngày mốc ban đầu không được trong tương lai.')

    @api.depends('service_reference_date', 'service_reference_odo', 'model_id',
        'service_interval_km', 'service_interval_months',
        'log_services.state', 'log_services.actual_end', 'log_services.maintenance_type',
        'log_services.service_odometer', 'log_services.service_odometer_recorded')
    def _compute_service_schedule(self):
        # Include archived completed services: archiving must not reset a milestone.
        services = self.env['fleet.vehicle.log.services'].sudo().with_context(active_test=False).search([
            ('vehicle_id', 'in', self.ids), ('state', '=', 'done'),
            ('maintenance_type', '=', 'preventive'), ('service_odometer_recorded', '=', True),
            ('actual_end', '!=', False)], order='actual_end desc, id desc')
        latest = {}
        for service in services:
            latest.setdefault(service.vehicle_id.id, service)
        for vehicle in self:
            date, odo = vehicle.service_reference_date, vehicle.service_reference_odo
            service = latest.get(vehicle.id)
            if service and (not date or service.actual_end.date() >= date):
                date, odo = service.actual_end.date(), service.service_odometer
            vehicle.service_last_date = date
            vehicle.service_last_odo = odo if date else 0
            vehicle.service_next_date = date + relativedelta(months=vehicle.service_interval_months) if date and vehicle.service_interval_months else False
            vehicle.service_next_odo = odo + vehicle.service_interval_km if date and vehicle.service_interval_km else 0

    def _maintenance_today(self):
        return fields.Date.context_today(self)

    @api.depends('service_last_date', 'service_next_date', 'service_next_odo', 'next_service_date',
        'odometer', 'is_electric_motorbike', 'service_interval_km',
        'service_interval_months', 'service_warning_km', 'service_warning_days')
    def _compute_service_alert(self):
        today = self._maintenance_today()
        for vehicle in self:
            configured = bool(vehicle.service_interval_km or vehicle.service_interval_months)
            state, reasons = 'ok', []
            levels = []
            # Existing manually appointed next_service_date remains an independent deadline.
            for date, label in [(vehicle.service_next_date, 'Hạn định kỳ'), (vehicle.next_service_date, 'Ngày hẹn bảo dưỡng')]:
                if date:
                    days = (date - today).days
                    level = 'overdue' if days < 0 else 'due' if days == 0 else 'soon' if days <= vehicle.service_warning_days else 'ok'
                    levels.append(level)
                    if level != 'ok':
                        detail = 'đã quá %s ngày' % abs(days) if days < 0 else 'đến hạn hôm nay' if days == 0 else 'còn %s ngày' % days
                        reasons.append('%s: %s (%s).' % (label, date, detail))
            if vehicle.service_last_date and vehicle.service_interval_km:
                remaining = vehicle.service_next_odo - vehicle.odometer
                level = 'overdue' if remaining < 0 else 'due' if remaining == 0 else 'soon' if remaining <= vehicle.service_warning_km else 'ok'
                levels.append(level)
                if level != 'ok':
                    reasons.append('ODO hiện tại %g km; mốc bảo dưỡng %g km (%s %g km).' % (
                        vehicle.odometer, vehicle.service_next_odo, 'vượt' if remaining < 0 else 'còn', abs(remaining)))
            rank = {'ok': 0, 'soon': 1, 'due': 2, 'overdue': 3}
            state = max(levels, key=rank.get) if levels else 'ok'
            if state == 'ok':
                if not configured and not vehicle.next_service_date:
                    state = 'unconfigured'
                elif configured and not vehicle.service_last_date:
                    state = 'missing_baseline'
            if configured and not vehicle.service_last_date:
                reasons.append('Chưa có mốc ban đầu đã xác minh; chưa thể tính đầy đủ kỳ bảo dưỡng.')
            if not vehicle.is_electric_motorbike:
                state, reasons = 'unconfigured', []
            vehicle.service_schedule_state = state
            vehicle.service_alert_message = '\n'.join(reasons)

    @api.model
    def _cron_refresh_service_alerts(self):
        vehicles = self.search([('is_electric_motorbike', '=', True)])
        for start in range(0, len(vehicles), 500):
            batch = vehicles[start:start + 500]
            batch._compute_service_alert()
            batch._auto_create_due_services()

    def _open_preventive_services(self):
        return self.env['fleet.vehicle.log.services'].search([
            ('vehicle_id', 'in', self.ids), ('maintenance_type', '=', 'preventive'),
            ('state', 'in', ['new', 'scheduled', 'running'])], order='id desc')

    @api.depends('log_services.state', 'log_services.maintenance_type', 'log_services.active')
    def _compute_open_preventive_count(self):
        for vehicle in self:
            vehicle.open_preventive_count = len(vehicle._open_preventive_services())

    def action_preventive_service(self):
        self.ensure_one()
        self.check_access('write')
        if not self.is_electric_motorbike or not self.active:
            raise UserError('Chỉ tạo bảo dưỡng cho xe điện đang khai thác.')
        # Serialize simultaneous clicks for this vehicle. Check as current user first.
        self.env.cr.execute('SELECT id FROM fleet_vehicle WHERE id=%s FOR UPDATE', (self.id,))
        existing = self._open_preventive_services()
        if existing:
            action = self.action_open_rental_services()
            action.update({'view_mode': 'form', 'views': [(False, 'form')], 'res_id': existing[0].id})
            return action
        self.env['fleet.vehicle.log.services'].check_access('create')
        service = self.env['fleet.vehicle.log.services'].create({
            'vehicle_id': self.id, 'maintenance_type': 'preventive',
            'description': 'Bảo dưỡng định kỳ — ' + (self.vehicle_code or self.display_name),
            'notes': self.service_alert_message or 'Nhân viên chủ động tạo phiếu bảo dưỡng định kỳ.',
            'blocks_rental': True})
        action = self.action_open_rental_services()
        action.update({'view_mode': 'form', 'views': [(False, 'form')], 'res_id': service.id})
        return action



class FleetServicePreventive(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    service_odometer = fields.Float('ODO lúc hoàn tất (km)', copy=False)
    service_odometer_recorded = fields.Boolean('Đã ghi nhận ODO hoàn tất', copy=False)

    @api.constrains('service_odometer', 'service_odometer_recorded', 'actual_end', 'maintenance_type')
    def _check_completion_odometer(self):
        for service in self:
            if service.service_odometer_recorded:
                if not math.isfinite(service.service_odometer) or service.service_odometer < 0:
                    raise ValidationError('ODO hoàn tất phải hữu hạn và không âm.')
                if service.service_odometer > service.vehicle_id.odometer:
                    raise ValidationError('ODO hoàn tất không được lớn hơn ODO hiện tại; cập nhật số đo xe trước.')

    def write(self, vals):
        vals = dict(vals)
        if any(service.state in ('done', 'cancelled') for service in self) and (
                {'service_odometer', 'service_odometer_recorded'} & vals.keys()):
            raise UserError('Không sửa ODO hoàn tất của phiếu đã kết thúc.')
        if 'service_odometer' in vals:
            vals['service_odometer_recorded'] = True
        finishing = self.filtered(lambda s: s.is_electric_motorbike and s.maintenance_type == 'preventive'
                                  and s.state == 'running') if vals.get('state') == 'done' else self.browse()
        if finishing:
            # Capture each vehicle separately; old historical services remain unqualified.
            for service in self:
                values = dict(vals)
                if service in finishing and not values.get('service_odometer_recorded', service.service_odometer_recorded):
                    values.update(service_odometer=service.vehicle_id.odometer, service_odometer_recorded=True)
                super(FleetServicePreventive, service).write(values)
                if service in finishing and not values.get('next_service_date', service.next_service_date):
                    # Consume an expired/manual appointment once periodic work is completed.
                    vehicle = service.vehicle_id
                    if vehicle.next_service_date and vehicle.next_service_date <= service.actual_end.date():
                        vehicle.next_service_date = False
            return True
        return super().write(vals)

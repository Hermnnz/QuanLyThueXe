import math
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_electric_motorbike = fields.Boolean('Xe máy điện', tracking=True)
    license_plate = fields.Char(copy=False)
    odometer = fields.Float(
        string='Số ODO hiện tại (km)', compute=None, inverse=None, store=True, default=0.0,
        help='Tổng số km xe đã chạy, tự động cập nhật sau mỗi chuyến thuê.')
    vehicle_code = fields.Char('Mã xe', copy=False, index=True)
    license_plate_key = fields.Char(compute='_compute_identity_keys', store=True, copy=False, index=True)
    vehicle_code_key = fields.Char(compute='_compute_identity_keys', store=True, copy=False, index=True)
    if hasattr(models, 'Constraint'):
        _vehicle_code_unique = models.Constraint('UNIQUE(vehicle_code)', 'Mã xe đã tồn tại.')
        _license_plate_unique = models.Constraint('UNIQUE(license_plate_key)', 'Biển số đã được sử dụng cho xe khác.')
        _normalized_code_unique = models.Constraint('UNIQUE(vehicle_code_key)', 'Mã xe đã tồn tại (không phân biệt hoa thường/khoảng trắng).')
    else:
        _sql_constraints = [
            ('vehicle_code_unique', 'UNIQUE(vehicle_code)', 'Mã xe đã tồn tại.'),
            ('license_plate_unique', 'UNIQUE(license_plate_key)', 'Biển số đã được sử dụng cho xe khác.'),
            ('normalized_code_unique', 'UNIQUE(vehicle_code_key)', 'Mã xe đã tồn tại (không phân biệt hoa thường/khoảng trắng).'),
        ]
    operational_status = fields.Selection([
        ('available', 'Sẵn sàng'), ('renting', 'Đang thuê'),
        ('pending_inspection', 'Chờ kiểm tra'), ('maintenance', 'Bảo dưỡng'),
        ('inactive', 'Ngừng hoạt động'),
    ], default='pending_inspection', required=True, copy=False, group_expand=True,
       string='Trạng thái vận hành', tracking=True)
    technical_ready = fields.Boolean('Đạt điều kiện kỹ thuật', default=False, copy=False, tracking=True)
    rental_blocked = fields.Boolean('Khóa thuê', tracking=True)
    block_reason = fields.Text('Lý do khóa')
    next_service_date = fields.Date('Ngày bảo dưỡng tiếp theo')

    @api.depends('license_plate', 'vehicle_code')
    def _compute_identity_keys(self):
        for vehicle in self:
            vehicle.license_plate_key = re.sub(r'[\W_]+', '', vehicle.license_plate or '').upper() or False
            vehicle.vehicle_code_key = ''.join((vehicle.vehicle_code or '').split()).upper() or False

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        for values in vals_list:
            values = dict(values)
            code = ''.join((values.get('vehicle_code') or '').split()).upper()
            while not code:
                candidate = self.env['ir.sequence'].next_by_code('motorbike.fleet.vehicle')
                if not candidate:
                    raise UserError('Chưa cấu hình bộ cấp mã phương tiện.')
                if not self.sudo().with_context(active_test=False).search_count([('vehicle_code_key', '=', candidate)]):
                    code = candidate
            values['vehicle_code'] = code
            if values.get('license_plate'):
                values['license_plate'] = values['license_plate'].strip().upper()
            vehicle_model = self.env['fleet.vehicle.model'].browse(values.get('model_id'))
            if vehicle_model and (not vehicle_model.active or not vehicle_model.brand_id.active):
                raise UserError('Không tạo xe từ hãng hoặc dòng xe đã ngừng sử dụng.')
            if values.get('active') is False or values.get('operational_status') == 'inactive':
                values.update(active=False, operational_status='inactive', technical_ready=False)
            prepared.append(values)
        return super().create(prepared)

    def write(self, vals):
        vals = dict(vals)
        if 'vehicle_code' in vals:
            vals['vehicle_code'] = ''.join((vals['vehicle_code'] or '').split()).upper()
            if not vals['vehicle_code']:
                raise ValidationError('Không được xóa mã phương tiện đã cấp.')
        if vals.get('license_plate'):
            vals['license_plate'] = vals['license_plate'].strip().upper()
        electric = self.filtered('is_electric_motorbike')
        if 'odometer' in vals and electric:
            new_odo = vals['odometer']
            if new_odo is not None and not isinstance(new_odo, bool) and isinstance(new_odo, (int, float)):
                for vehicle in electric:
                    if new_odo < vehicle.odometer:
                        raise ValidationError('Không được điều chỉnh lùi số ODO hiện tại của xe.')
        if vals.get('operational_status') == 'inactive':
            vals['active'] = False
        if vals.get('active') is False and electric:
            if electric.filtered(lambda v: v.operational_status in ('renting', 'maintenance')) or electric._running_blocking_services():
                raise UserError('Nhận trả xe và hoàn tất/hủy phiếu đang thực hiện trước khi ngừng hoạt động.')
            vals.update(operational_status='inactive', technical_ready=False)
        elif vals.get('active') is True and electric.filtered(lambda v: not v.active):
            if self.filtered('active'):
                raise UserError('Chỉ khôi phục các xe ngừng hoạt động trong cùng một thao tác.')
            vals.update(operational_status='pending_inspection', technical_ready=False)
        for vehicle in electric:
            if vals.get('active') is False and vehicle.operational_status == 'renting':
                raise UserError('Không ngừng sử dụng xe đang thuê; cần nhận trả trước.')
            if vals.get('is_electric_motorbike') is False:
                if (vehicle.operational_status in ('renting', 'maintenance')
                        or self.env['fleet.vehicle.log.services'].sudo().with_context(active_test=False).search_count([
                            ('vehicle_id', '=', vehicle.id)])):
                    raise UserError('Không đổi phân loại xe khi đang thuê hoặc đã có hồ sơ bảo dưỡng, kể cả hồ sơ lưu trữ.')
            if vehicle.operational_status != 'available' and vals.get('operational_status') == 'available':
                raise ValidationError('Dùng nghiệp vụ nhận trả hoặc nút xác nhận đạt kỹ thuật để đưa xe về Sẵn sàng.')
        if 'model_id' in vals:
            model = self.env['fleet.vehicle.model'].browse(vals['model_id'])
            if model and (not model.active or not model.brand_id.active):
                raise UserError('Không chọn hãng hoặc dòng xe đã ngừng sử dụng.')
        return super().write(vals)

    def _write_operational_state(self, values):
        """Private workflow entry; cannot be called through public RPC methods."""
        self.check_access('write')
        return super().write(values)

    def unlink(self):
        # Preserve vehicle identity and all business references, even for sudo.
        raise UserError('Không được xóa phương tiện trong bất kỳ trường hợp nào. Hãy dùng Lưu trữ / Ngừng sử dụng.')

    @api.constrains('odometer', 'is_electric_motorbike')
    def _check_current_odometer(self):
        for vehicle in self.filtered('is_electric_motorbike'):
            if not math.isfinite(vehicle.odometer) or vehicle.odometer < 0:
                raise UserError('ODO hiện tại phải là số hữu hạn, không âm.')

    def action_open_rental_services(self):
        self.ensure_one()
        self.check_access('read')
        action = self.env['ir.actions.actions']._for_xml_id(
            'motorbike_fleet_management.action_motorbike_services')
        action['domain'] = [('vehicle_id', '=', self.id)]
        action['context'] = {'motorbike_only': True, 'default_vehicle_id': self.id}
        return action

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
            if (vehicle.operational_status == 'inactive') != (not vehicle.active):
                raise ValidationError('Xe ngừng hoạt động phải được lưu trữ; khôi phục xe phải kiểm tra kỹ thuật lại.')
            if vehicle.operational_status == 'inactive' and vehicle.technical_ready:
                raise ValidationError('Xe ngừng hoạt động không được đánh dấu đạt kỹ thuật.')
            if vehicle.operational_status == 'available' and not vehicle.technical_ready:
                raise ValidationError('Xe sẵn sàng phải đạt điều kiện kỹ thuật.')
            if vehicle.operational_status in ('pending_inspection', 'maintenance') and vehicle.technical_ready:
                raise ValidationError('Xe chờ kiểm tra hoặc bảo dưỡng chưa được đánh dấu đạt kỹ thuật.')
            if vehicle._running_blocking_services() and (
                    vehicle.operational_status != 'maintenance' or vehicle.technical_ready):
                raise ValidationError('Xe đang bảo dưỡng chặn thuê phải ở trạng thái bảo dưỡng và chưa đạt kỹ thuật.')

    def action_confirm_technical_ready(self):
        self.check_access('write')
        for vehicle in self:
            if not vehicle.is_electric_motorbike or not vehicle.active:
                raise UserError('Chỉ xác nhận kỹ thuật cho xe điện đang khai thác.')
            if vehicle.operational_status == 'renting':
                raise UserError('Không xác nhận sẵn sàng khi xe đang được thuê.')
            if vehicle._running_blocking_services():
                raise UserError('Còn bảo dưỡng đang thực hiện và chặn thuê.')
        return self._write_operational_state({'technical_ready': True, 'operational_status': 'available'})

    @api.model
    def _rental_period(self, start, end):
        try:
            start, end = fields.Datetime.to_datetime(start), fields.Datetime.to_datetime(end)
        except (TypeError, ValueError):
            raise ValidationError('Thời gian thuê phải là Datetime hợp lệ.')
        if not start or not end or start.tzinfo or end.tzinfo or start >= end:
            raise ValidationError('Khoảng thuê cần bắt đầu trước kết thúc, theo Datetime UTC của Odoo.')
        return start, end

    def _maintenance_overlaps(self, start, end):
        self.ensure_one()
        # Only work already in progress blocks rental. Drafts reserve no time.
        return any(not service.actual_start or service.actual_start < end
                   for service in self._running_blocking_services())

    def check_fleet_availability(self, start, end):
        """Fleet eligibility only. Rental must also check its confirmed/renting contracts.

        Intervals are [start, end), UTC. Current 'renting' does not by itself block
        a future booking: the contract's actual reservation interval owns that check.
        """
        self.check_access('read')
        start, end = self._rental_period(start, end)
        result = []
        for vehicle in self:
            reasons = []
            if not vehicle.is_electric_motorbike:
                reasons.append('not_electric_motorbike')
            if not vehicle.active:
                reasons.append('archived')
            if not vehicle.model_id.active or not vehicle.model_id.brand_id.active:
                reasons.append('inactive_catalog')
            if not vehicle.technical_ready:
                reasons.append('not_technical_ready')
            if vehicle.rental_blocked:
                reasons.append('rental_blocked')
            if vehicle._maintenance_overlaps(start, end):
                reasons.append('blocking_maintenance')
            result.append({'vehicle_id': vehicle.id, 'fleet_ok': not reasons, 'reasons': reasons})
        return result

    def _record_operation_odometer(self, value, measured_at):
        self.ensure_one()
        if value is None:
            return
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValidationError('ODO phải là một số hữu hạn.')
        # Refresh stored ODO before validating a supplied Operations measurement.
        self.invalidate_recordset(['odometer', 'odometer_count'])
        if value < 0 or value < self.odometer:
            raise ValidationError('ODO giao/trả không được âm hoặc thấp hơn ODO hiện tại của xe.')
        try:
            measured_at = fields.Datetime.to_datetime(measured_at) if measured_at else fields.Datetime.now()
        except (TypeError, ValueError):
            raise ValidationError('Thời gian ghi nhận ODO không hợp lệ.')
        if not measured_at or measured_at.tzinfo:
            raise ValidationError('Thời gian ghi nhận ODO phải theo Datetime UTC của Odoo.')
        logs = self.env['fleet.vehicle.odometer']
        existing = logs.search([('vehicle_id', '=', self.id), ('date', '=', measured_at.date()),
                                ('value', '=', value)], limit=1)
        if not existing:
            logs.create({'vehicle_id': self.id, 'value': value, 'date': measured_at.date()})
        self.odometer = value
        self.invalidate_recordset(['odometer', 'odometer_count'])

    def action_deliver_vehicle(self, rental_start, rental_end, odometer_start=None, checkout_at=None):
        """Called by Operations after Rental has validated the booking and payment conditions."""
        self.ensure_one()
        self.check_access('write')
        eligibility = self.check_fleet_availability(rental_start, rental_end)[0]
        if not eligibility['fleet_ok']:
            raise UserError('Xe chưa đủ điều kiện Fleet để giao: ' + ', '.join(eligibility['reasons']))
        if self.operational_status != 'available':
            raise UserError('Chỉ giao xe đang ở trạng thái sẵn sàng.')
        # Query and validate before changing either state or ODO.
        self._record_operation_odometer(odometer_start, checkout_at)
        return self.write({'operational_status': 'renting'})

    def action_return_vehicle(self, inspection_result, odometer_end=None, checkin_at=None):
        """An explicit result is required; receipt of a vehicle alone is not a technical pass.

        Operations owns trip ODO/battery snapshots, notes and duplicate-submit protection.
        This method must be called in the same transaction as confirmation of its return line.
        """
        self.ensure_one()
        self.check_access('write')
        if not self.is_electric_motorbike or not self.active:
            raise UserError('Chỉ nhận trả cho xe điện đang khai thác.')
        if self.operational_status not in ('renting', 'maintenance'):
            raise UserError('Xe không ở trạng thái đang thuê hoặc đang xử lý bảo dưỡng.')
        if inspection_result not in ('passed', 'failed', 'pending', 'maintenance'):
            raise ValidationError('Kết quả trả xe phải là passed, failed, pending hoặc maintenance.')
        if self._running_blocking_services() or inspection_result == 'maintenance':
            values = {'operational_status': 'maintenance', 'technical_ready': False}
        elif inspection_result == 'passed':
            values = {'operational_status': 'available', 'technical_ready': True}
        else:
            values = {'operational_status': 'pending_inspection', 'technical_ready': False}
        self._record_operation_odometer(odometer_end, checkin_at)
        # A voluntary rental block and its reason are retained even for a passed return.
        return self._write_operational_state(values)

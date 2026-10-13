import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    is_electric_motorbike = fields.Boolean('Xe máy điện', tracking=True)
    odometer = fields.Float(
        string='Số ODO hiện tại (km)',
        default=0.0,
        help='Tổng số km xe đã chạy, tự động cập nhật sau mỗi chuyến thuê.',
    )
    vehicle_code = fields.Char('Mã xe', copy=False, index=True)
    _vehicle_code_unique = models.Constraint(
        'UNIQUE(vehicle_code)', 'Mã xe đã tồn tại. Vui lòng sử dụng mã xe khác.')
    operational_status = fields.Selection([
        ('available', 'Sẵn sàng'), ('renting', 'Đang thuê'),
        ('pending_inspection', 'Chờ kiểm tra'), ('maintenance', 'Bảo dưỡng'),
    ], default='pending_inspection', required=True, copy=False, group_expand=True,
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
            if vehicle.operational_status == 'renting':
                raise UserError('Không xác nhận sẵn sàng khi xe đang được thuê.')
            if vehicle._running_blocking_services():
                raise UserError('Còn bảo dưỡng đang thực hiện và chặn thuê.')
        return self.write({'technical_ready': True, 'operational_status': 'available'})

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
        services = self.env['fleet.vehicle.log.services'].sudo().search([
            ('vehicle_id', '=', self.id), ('active', '=', True), ('blocks_rental', '=', True),
            ('state', 'in', ['scheduled', 'running'])])
        for service in services:
            if service.state == 'running':
                # An unfinished job has no guaranteed release time; a planned end is not completion.
                actual_start = service.actual_start or service.scheduled_start
                if not actual_start or actual_start < end:
                    return True
            elif service.scheduled_start and service.scheduled_end and (
                    service.scheduled_start < end and service.scheduled_end > start):
                return True
        return False

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
        # Native odometer is a non-stored compute without log dependencies.
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
        return self.write(values)

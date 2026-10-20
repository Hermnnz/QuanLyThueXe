from lxml import etree
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


def staff_only(env):
    return (not env.su and env.user.has_group('motorbike_fleet_management.group_fleet_staff')
            and not env.user.has_group('fleet.fleet_group_manager'))


def staff_view(result, env):
    if staff_only(env):
        result = dict(result)
        root = etree.fromstring(result['arch'].encode())
        root.set('edit', 'false')
        root.set('delete', 'false')
        result['arch'] = etree.tostring(root, encoding='unicode')
    return result


class FleetVehicleRoles(models.Model):
    _inherit = 'fleet.vehicle'

    @api.model_create_multi
    def create(self, vals_list):
        if staff_only(self.env):
            for values in vals_list:
                if (values.get('operational_status', 'pending_inspection') != 'pending_inspection'
                        or values.get('technical_ready') or values.get('active') is False):
                    raise AccessError('Nhân viên chỉ tạo xe mới chờ kiểm tra, không tự xác nhận kỹ thuật/ngừng hoạt động.')
        vehicles = super().create(vals_list)
        if staff_only(self.env) and vehicles.filtered(lambda v:
                v.operational_status != 'pending_inspection' or v.technical_ready or not v.active):
            raise AccessError('Xe do nhân viên tạo phải đang hoạt động và chờ kiểm tra kỹ thuật.')
        return vehicles

    def write(self, vals):
        if staff_only(self.env):
            raise AccessError('Nhân viên không được sửa hồ sơ hoặc lưu trữ/khôi phục phương tiện.')
        return super().write(vals)

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        return staff_view(super().get_view(view_id, view_type, **options), self.env)

    def _write_operational_state(self, values):
        if staff_only(self.env):
            raise AccessError('Nhân viên chỉ thay đổi trạng thái xe qua Bắt đầu/Hoàn tất phiếu bảo dưỡng.')
        return super()._write_operational_state(values)

    def action_confirm_technical_ready(self):
        if staff_only(self.env):
            raise AccessError('Chỉ quản lý được xác nhận kỹ thuật ngoài quy trình hoàn tất bảo dưỡng.')
        return super().action_confirm_technical_ready()


class FleetServiceRoles(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    @api.model_create_multi
    def create(self, vals_list):
        if staff_only(self.env):
            for values in vals_list:
                vehicle = self.env['fleet.vehicle'].browse(values.get('vehicle_id') or self.env.context.get('default_vehicle_id'))
                vehicle.check_access('read')
                if vehicle and (not vehicle.is_electric_motorbike or not vehicle.active):
                    raise AccessError('Nhân viên chỉ tạo phiếu cho xe điện đang hoạt động và được quyền xem.')
                if values.get('state', self.env.context.get('default_state', 'new')) != 'new' or values.get('active') is False:
                    raise AccessError('Nhân viên chỉ được tạo phiếu Mới, không nhập phiếu lịch sử hay bắt đầu qua import.')
        services = super().create(vals_list)
        if staff_only(self.env):
            for service in services:
                service.vehicle_id.check_access('read')
                if (service.state != 'new' or not service.active or not service.vehicle_id.active
                        or not service.is_electric_motorbike):
                    raise AccessError('Nhân viên chỉ tạo phiếu Mới cho xe điện đang hoạt động.')
        return services

    def write(self, vals):
        if staff_only(self.env):
            raise AccessError('Nhân viên không được sửa phiếu; dùng nút Bắt đầu hoặc Hoàn tất.')
        return super().write(vals)

    def unlink(self):
        if staff_only(self.env):
            raise AccessError('Nhân viên không được xóa phiếu bảo dưỡng.')
        return super().unlink()

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        return staff_view(super().get_view(view_id, view_type, **options), self.env)

    def _check_staff_service_action(self):
        self.ensure_one()
        if not staff_only(self.env):
            raise AccessError('Thao tác này dành cho nhân viên theo quy trình.')
        self.check_access('read')
        self.vehicle_id.check_access('read')
        self.env.cr.execute('SELECT id FROM fleet_vehicle_log_services WHERE id=%s FOR UPDATE', (self.id,))
        self.invalidate_recordset()
        if not self.is_electric_motorbike or not self.active or not self.vehicle_id.active:
            raise UserError('Chỉ xử lý phiếu đang sử dụng cho xe điện đang hoạt động.')

    def action_start(self):
        if staff_only(self.env):
            self._check_staff_service_action()
            if self.state != 'new':
                raise UserError('Chỉ bắt đầu phiếu Mới.')
            return self.sudo().action_start()
        return super().action_start()

    def action_done(self):
        if staff_only(self.env):
            self._check_staff_service_action()
            if self.state != 'running':
                raise UserError('Chỉ hoàn tất phiếu đang thực hiện.')
            return {'type': 'ir.actions.act_window', 'name': 'Hoàn tất bảo dưỡng',
                    'res_model': 'motorbike.service.complete.wizard', 'view_mode': 'form', 'target': 'new',
                    'context': {'default_service_id': self.id, 'default_result': self.result or ''}}
        return super().action_done()

    def action_cancel(self):
        if staff_only(self.env):
            raise AccessError('Chỉ quản lý được hủy phiếu bảo dưỡng.')
        return super().action_cancel()


class ServiceCompleteWizard(models.TransientModel):
    _name = 'motorbike.service.complete.wizard'
    _description = 'Nhân viên xác nhận hoàn tất bảo dưỡng'

    service_id = fields.Many2one('fleet.vehicle.log.services', required=True, readonly=True)
    result = fields.Text('Kết quả công việc', required=True)

    def action_complete(self):
        self.ensure_one()
        if self.create_uid != self.env.user:
            raise AccessError('Chỉ người tạo được xác nhận hộp thoại này.')
        self.service_id._check_staff_service_action()
        if self.service_id.state != 'running':
            raise UserError('Phiếu không còn đang thực hiện.')
        if not (self.result or '').strip():
            raise UserError('Nhập kết quả công việc trước khi hoàn tất.')
        self.service_id.sudo().write({'result': self.result.strip(), 'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}


class FleetOdometerRoles(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    def write(self, vals):
        if staff_only(self.env):
            raise AccessError('Nhân viên không được sửa lịch sử ODO.')
        return super().write(vals)

    def unlink(self):
        if staff_only(self.env):
            raise AccessError('Nhân viên không được xóa lịch sử ODO.')
        return super().unlink()

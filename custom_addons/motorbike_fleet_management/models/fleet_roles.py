from lxml import etree

from odoo import api, fields, models

from odoo.exceptions import AccessError, UserError





def staff_only(env):

    """Kiểm tra người dùng hiện tại có phải là Nhân viên quản lý xe thuần túy hay không."""
    return (not env.su and env.user.has_group('motorbike_fleet_management.group_fleet_staff')

            and not env.user.has_group('fleet.fleet_group_manager'))





def staff_view(result, env):

    """Ẩn nút Xóa trên giao diện form đối với vai trò Nhân viên quản lý xe."""
    if staff_only(env):

        result = dict(result)

        root = etree.fromstring(result['arch'].encode())

        root.set('delete', 'false')

        result['arch'] = etree.tostring(root, encoding='unicode')

    return result





class FleetVehicleRoles(models.Model):

    """Ma trận kiểm soát quyền hạn giữa Admin, Quản lý xe và Nhân viên trên hồ sơ xe."""
    _inherit = 'fleet.vehicle'



    @api.model_create_multi

    def create(self, vals_list):

        """Chốt chặn nhân viên chỉ được tạo xe mới ở trạng thái Chờ kiểm tra kỹ thuật."""
        if staff_only(self.env):

            for values in vals_list:

                if (values.get('operational_status', 'pending_inspection') != 'pending_inspection'

                        or values.get('technical_ready') or values.get('active') is False):

                    raise AccessError('Nhân viên chỉ tạo xe mới chờ kiểm tra, không tự xác nhận kỹ thuật/ngừng hoạt động.')

        vehicles = super().create(vals_list)

        if staff_only(self.env) and any(

                vehicle.operational_status != 'pending_inspection' or vehicle.technical_ready or not vehicle.active for vehicle in vehicles):

            raise AccessError('Xe do nhân viên tạo phải đang hoạt động và chờ kiểm tra kỹ thuật.')

        return vehicles



    def write(self, vals):
        """Chặn nhân viên tự đổi trạng thái kỹ thuật hoặc sửa thông tin xe đang thuê/bảo dưỡng."""
        if staff_only(self.env) and not self.env.user.has_group('motorbike_fleet_management.group_motorbike_technician'):
            disallowed = {'operational_status', 'technical_ready', 'active', 'pre_maintenance_status', 'rental_blocked', 'block_reason'}
            if set(vals) & disallowed:
                raise AccessError('Nhân viên không được tự ý đổi trạng thái kỹ thuật hoặc lưu trữ/khóa xe.')
            for vehicle in self:
                if vehicle.operational_status in ('renting', 'maintenance'):
                    raise UserError('Xe đang thuê hoặc đang bảo dưỡng; nhân viên không được sửa thông tin.')
        return super().write(vals)



    @api.model

    def get_view(self, view_id=None, view_type='form', **options):

        """Can thiệp giao diện form xe để loại bỏ nút Xóa đối với nhân viên thường."""
        return staff_view(super().get_view(view_id, view_type, **options), self.env)



    def _write_operational_state(self, values):

        """Chặn nhân viên đổi trạng thái xe trực tiếp ngoài quy trình Bắt đầu/Hoàn tất bảo dưỡng."""
        if staff_only(self.env) and not self.env.user.has_group('motorbike_fleet_management.group_motorbike_technician'):

            raise AccessError('Nhân viên chỉ thay đổi trạng thái xe qua Bắt đầu/Hoàn tất phiếu bảo dưỡng.')

        return super()._write_operational_state(values)



    def action_confirm_technical_ready(self):

        """Chỉ cho phép Quản lý xe hoặc Kỹ thuật viên xác nhận xe đạt điều kiện kỹ thuật."""
        if staff_only(self.env) and not self.env.user.has_group('motorbike_fleet_management.group_motorbike_technician'):

            raise AccessError('Chỉ quản lý hoặc kỹ thuật viên được xác nhận kỹ thuật.')

        return super().action_confirm_technical_ready()





class FleetServiceRoles(models.Model):

    """Kiểm soát quyền nhận việc, bắt đầu, hoàn tất và hủy bỏ phiếu bảo dưỡng."""
    _inherit = 'fleet.vehicle.log.services'



    @api.model_create_multi

    def create(self, vals_list):

        """Chốt chặn nhân viên chỉ tạo phiếu Mới cho xe điện đang hoạt động."""
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
        """Chặn nhân viên sửa trạng thái, kỹ thuật viên phụ trách hoặc chi phí phiếu bảo dưỡng."""
        if staff_only(self.env) and not self.env.user.has_group('motorbike_fleet_management.group_motorbike_technician'):
            disallowed = {'state', 'technician_id', 'amount', 'cost', 'next_service_date', 'actual_start', 'actual_end', 'blocks_rental', 'active'}
            if set(vals) & disallowed:
                raise AccessError('Nhân viên không được sửa trạng thái, thợ phụ trách hoặc chi phí phiếu bảo dưỡng.')
            for service in self:
                if service.state in ('running', 'done', 'cancelled'):
                    raise UserError('Phiếu đang thực hiện hoặc đã kết thúc; nhân viên không được chỉnh sửa.')
        return super().write(vals)



    def unlink(self):

        """Cấm nhân viên xóa hồ sơ phiếu bảo dưỡng."""
        if staff_only(self.env):

            raise AccessError('Nhân viên không được xóa phiếu bảo dưỡng.')

        return super().unlink()



    @api.model

    def get_view(self, view_id=None, view_type='form', **options):

        """Ẩn nút Xóa trên giao diện phiếu bảo dưỡng đối với nhân viên thường."""
        return staff_view(super().get_view(view_id, view_type, **options), self.env)



    def _check_staff_service_action(self):

        """Khóa hàng cơ sở dữ liệu và kiểm tra quyền nhân viên trước khi thao tác phiếu."""
        self.ensure_one()

        if not staff_only(self.env):

            raise AccessError('Thao tác này dành cho nhân viên theo quy trình.')

        self.check_access('read')

        self.vehicle_id.check_access('read')

        self.env.cr.execute('SELECT id FROM fleet_vehicle_log_services WHERE id=%s FOR UPDATE', (self.id,))

        self.invalidate_recordset()

        if not self.is_electric_motorbike or not self.active or not self.vehicle_id.active:

            raise UserError('Chỉ xử lý phiếu đang sử dụng cho xe điện đang hoạt động.')



    def action_claim_ticket(self):
        """Kỹ thuật viên tự nhận phiếu Mới để thực hiện sửa chữa."""
        if staff_only(self.env):
            self._check_staff_service_action()
            if self.state != 'new':
                raise UserError('Chỉ có thể nhận các phiếu đang ở trạng thái Mới.')
            return self.sudo().write({
                'technician_id': self.env.user.partner_id.id,
                'state': 'running',
            })
        return super().action_claim_ticket()

    def action_start(self):

        """Chuyển phiếu Mới sang Đang thực hiện khi đã có kỹ thuật viên phụ trách."""
        if staff_only(self.env):

            self._check_staff_service_action()

            if self.state != 'new':

                raise UserError('Chỉ bắt đầu phiếu Mới.')

            return self.sudo().action_start()

        return super().action_start()



    def action_done(self):

        """Mở hộp thoại bắt buộc nghiệm thu kết quả công việc trước khi hoàn tất bảo dưỡng."""
        if staff_only(self.env):

            self._check_staff_service_action()

            if self.state != 'running':

                raise UserError('Chỉ hoàn tất phiếu đang thực hiện.')

            return {'type': 'ir.actions.act_window', 'name': 'Hoàn tất bảo dưỡng',

                    'res_model': 'motorbike.service.complete.wizard', 'view_mode': 'form', 'target': 'new',

                    'context': {'default_service_id': self.id, 'default_result': self.result or ''}}

        return super().action_done()



    def action_cancel(self):

        """Chỉ cấp Quản lý xe mới có quyền hủy bỏ phiếu bảo dưỡng."""
        if staff_only(self.env):

            raise AccessError('Chỉ quản lý được hủy phiếu bảo dưỡng.')

        return super().action_cancel()





class ServiceCompleteWizard(models.TransientModel):

    """Hộp thoại Wizard bắt buộc nhập kết quả nghiệm thu khi kết thúc bảo dưỡng."""
    _name = 'motorbike.service.complete.wizard'

    _description = 'Nhân viên xác nhận hoàn tất bảo dưỡng'



    service_id = fields.Many2one('fleet.vehicle.log.services', required=True, readonly=True)

    result = fields.Text('Kết quả công việc', required=True)



    def action_complete(self):

        """Lưu kết quả nghiệm thu công việc và đóng phiếu sang trạng thái Hoàn tất."""
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

    """Bảo mật công-tơ-mét: Cấm nhân viên chỉnh sửa hoặc xóa lịch sử ODO."""
    _inherit = 'fleet.vehicle.odometer'



    def write(self, vals):

        """Cấm nhân viên chỉnh sửa lịch sử chỉ số ODO đã ghi nhận."""
        if staff_only(self.env):

            raise AccessError('Nhân viên không được sửa lịch sử ODO.')

        return super().write(vals)



    def unlink(self):

        """Cấm nhân viên xóa bản ghi lịch sử chỉ số ODO."""
        if staff_only(self.env):

            raise AccessError('Nhân viên không được xóa lịch sử ODO.')

        return super().unlink()


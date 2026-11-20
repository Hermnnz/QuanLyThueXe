# -*- coding: utf-8 -*-
"""Wizard Cập nhật nhanh Địa điểm & Thời gian Giao/Thu hồi Xe (TransientModel).

- Cho phép chọn nhiều dòng xe trên Phiếu vận hành và cập nhật hàng loạt cùng lúc:
  + Ngày/giờ giao xe và địa điểm giao xe.
  + Ngày/giờ thu hồi xe và địa điểm thu hồi xe.
- Tự động kiểm tra bỏ qua hoặc báo lỗi nếu xe đã giao/đã thu hồi không được phép sửa lịch.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# WIZARD CẬP NHẬT NHANH ĐỊA ĐIỂM & GIỜ GIAO/THU HỒI CHO NHIỀU XE
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class RentalVehicleScheduleWizard(models.TransientModel): # Model tạm cho popup sửa lịch nhanh
    _name = 'rental.vehicle.schedule.wizard'
    _description = 'Cập nhật Địa điểm & Thời gian Giao/Thu hồi Xe'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành')
    vehicle_ids = fields.Many2many( # Danh sách các dòng xe được chọn từ phiếu vận hành
        'rental.operation.ticket.vehicle',
        'rental_veh_sched_wiz_vehicle_rel',
        'wizard_id',
        'vehicle_id',
        string='Xe được chọn'
    )
    vehicle_count = fields.Integer(string='Số lượng xe', compute='_compute_vehicle_count') # Đếm số xe đang chọn để hiển thị trên popup

    # <<<< 4 trường nhập thông tin lịch mới (được khởi tạo giá trị mặc định qua context từ dòng xe đầu tiên)
    delivery_location = fields.Char(
        string='Địa điểm giao xe', 
        default='Tại cửa hàng',
        help='Địa điểm giao xe cho các xe được chọn'
    )
    delivery_time = fields.Char(
        string='Giờ giao xe', 
        placeholder='VD: 08:30 hoặc 14:00',
        help='Thời gian giao xe dự kiến (VD: 08:30)'
    )
    return_location = fields.Char(
        string='Địa điểm thu hồi xe', 
        default='Tại cửa hàng',
        help='Địa điểm thu hồi xe cho các xe được chọn'
    )
    return_time = fields.Char(
        string='Giờ thu hồi xe', 
        placeholder='VD: 12:00 hoặc 18:00',
        help='Thời gian thu hồi xe dự kiến (VD: 18:00)'
    )

    @api.depends('vehicle_ids')
    def _compute_vehicle_count(self): # Tính tổng số lượng xe được tick chọn
        for rec in self:
            rec.vehicle_count = len(rec.vehicle_ids)

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # HÀM ÁP DỤNG LỊCH MỚI XUỐNG TỪNG XE VÀ ĐỒNG BỘ VÀO BIÊN LAI CHƯA HOÀN TẤT
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def action_apply(self):
        self.ensure_one()
        if not self.vehicle_ids: # Chặn nếu không có xe nào được truyền vào wizard
            raise UserError('Không có xe nào được chọn để cập nhật!')

        # <<<< 1. Cập nhật xuống từng dòng xe con (đặt cờ is_custom_... = True để không bị thiết lập chung của phiếu ghi đè)
        for veh in self.vehicle_ids:
            veh_vals = {}
            # Xe chưa giao mới được sửa thông tin giao xe (địa điểm & giờ giao)
            if veh.status in ('waiting', 'delivering'):
                if self.delivery_location and self.delivery_location != veh.delivery_location:
                    veh_vals['delivery_location'] = self.delivery_location
                    veh_vals['is_custom_delivery_location'] = True # Bật cờ tùy chỉnh riêng
                if self.delivery_time and self.delivery_time != veh.delivery_time:
                    veh_vals['delivery_time'] = self.delivery_time
                    veh_vals['is_custom_delivery_time'] = True # Bật cờ tùy chỉnh riêng

            # Xe chưa thu hồi (chờ giao, đang giao hoặc đang thuê) được phép sửa thông tin thu hồi (địa điểm & giờ thu hồi)
            if veh.status != 'returned':
                if self.return_location and self.return_location != veh.return_location:
                    veh_vals['return_location'] = self.return_location
                    veh_vals['is_custom_return_location'] = True # Bật cờ tùy chỉnh riêng
                if self.return_time and self.return_time != veh.return_time:
                    veh_vals['return_time'] = self.return_time
                    veh_vals['is_custom_return_time'] = True # Bật cờ tùy chỉnh riêng

            if veh_vals: # Chỉ gọi write xuống DB khi thực sự có trường thay đổi
                veh.write(veh_vals)

        # <<<< 2. Đồng bộ trực tiếp vào các biên lai giao xe chưa hoàn tất (nếu có)
        receipts_to_update = self.vehicle_ids.mapped('delivery_receipt_id').filtered(lambda r: r.state != 'delivered') # Bỏ qua biên lai đã giao thành công
        for r in receipts_to_update:
            r_vals = {}
            if self.delivery_location:
                r_vals['delivery_location'] = self.delivery_location
            if self.delivery_time:
                r_vals['delivery_time'] = self.delivery_time
            if r_vals:
                r.write(r_vals)

        # <<<< 3. Đồng bộ trực tiếp vào các biên lai thu hồi xe chưa hoàn tất (nếu có)
        ret_receipts_to_update = self.vehicle_ids.mapped('return_receipt_id').filtered(lambda r: r.state != 'returned') # Bỏ qua biên lai đã thu hồi hoàn tất
        for r in ret_receipts_to_update:
            r_vals = {}
            if self.return_location:
                r_vals['return_location'] = self.return_location
            if self.return_time:
                r_vals['return_time'] = self.return_time
            if r_vals:
                r.write(r_vals)

        # Bỏ tick chọn sau khi cập nhật thành công
        self.vehicle_ids.write({'is_selected': False})
        return {'type': 'ir.actions.act_window_close'} # Đóng popup modal
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

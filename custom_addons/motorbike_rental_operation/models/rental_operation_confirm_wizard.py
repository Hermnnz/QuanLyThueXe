# -*- coding: utf-8 -*-
"""Wizard Xác nhận Thao tác Vận hành Xe hàng loạt (TransientModel).

- Hiển thị hộp thoại xác nhận trước khi thực hiện thao tác hàng loạt trên nhiều xe:
  + Bắt đầu giao xe (start_delivery)
  + Xác nhận đã giao xe (confirm_delivery)
  + Xác nhận thu hồi xe (confirm_return)
- Giúp tránh bấm nhầm và tóm tắt danh sách xe chuẩn bị chuyển trạng thái.
"""

from odoo import models, fields, api

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# WIZARD POPUP XÁC NHẬN THAO TÁC HÀNG LOẠT TRÊN NHIỀU XE (TRANSIENT MODEL)
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class RentalOperationConfirmWizard(models.TransientModel): # TransientModel: model tạm phục vụ popup, Odoo tự dọn rác định kỳ
    _name = 'rental.operation.confirm.wizard'
    _description = 'Xác nhận Thao tác Vận Hành Xe'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành') # Phiếu vận hành đang mở popup này
    action_type = fields.Selection([ # Loại thao tác cần xác nhận (được truyền qua context từ nút bấm bên ticket)
        ('start_delivery', 'Bắt đầu giao xe'),
        ('confirm_delivery', 'Xác nhận đã giao xe'),
        ('confirm_return', 'Xác nhận thu hồi xe'),
    ], string='Loại thao tác', required=True)
    vehicle_ids = fields.Many2many( # Danh sách các dòng xe được tick chọn để thực thi hàng loạt
        'rental.operation.ticket.vehicle',
        'rental_op_confirm_veh_rel', # Tên bảng trung gian trong DB
        'wizard_id',
        'vehicle_id',
        string='Danh sách xe',
    )
    message = fields.Text(string='Nội dung xác nhận', readonly=True) # Câu hỏi xác nhận hiển thị trên popup (chỉ đọc)

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # HÀM XÁC NHẬN THỰC THI THAO TÁC HÀNG LOẠT LÊN CÁC XE ĐÃ CHỌN
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def action_apply(self):
        self.ensure_one()
        # <<<< Dựa vào action_type để gọi đúng hàm nghiệp vụ tương ứng trên model rental.operation.ticket.vehicle
        if self.action_type == 'start_delivery':
            self.vehicle_ids.action_start_delivery() # Chuyển các xe sang Đang giao ('delivering')
        elif self.action_type == 'confirm_delivery':
            self.vehicle_ids.action_confirm_delivery() # Chuyển các xe sang Đang thuê ('renting')
        elif self.action_type == 'confirm_return':
            self.vehicle_ids.action_confirm_return() # Chuyển các xe sang Đã thu hồi ('returned')
        return {'type': 'ir.actions.act_window_close'} # Đóng popup modal sau khi hoàn tất
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

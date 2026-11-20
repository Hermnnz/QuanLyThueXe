# -*- coding: utf-8 -*-
"""Wizard Xác nhận & Xuất Biên lai Thu hồi Xe (TransientModel).

- Cho phép nhân viên kiểm đếm lại phụ kiện khách trả, ghi chú tình trạng ngoại quan/trầy xước
  khi nhận lại xe và chia nhóm tạo hoặc cập nhật Biên lai thu hồi xe.
- Hỗ trợ xuất báo cáo PDF biên bản thu hồi ngay sau khi lưu biên lai.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# WIZARD KIỂM ĐẾM PHỤ KIỆN, NGOẠI QUAN & XUẤT BIÊN LAI THU HỒI XE (TỐI ĐA 6 TAB NHÓM XE)
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class RentalReturnReceiptWizard(models.TransientModel):
    _name = 'rental.return.receipt.wizard'
    _description = 'Xác Nhận & Xuất Biên Lai Thu Hồi Xe'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', required=True)
    customer_id = fields.Many2one('res.partner', string='Khách hàng', related='ticket_id.customer_id', readonly=True) # Tự lấy khách hàng từ phiếu vận hành
    customer_phone = fields.Char(string='Số điện thoại', related='ticket_id.customer_phone', readonly=True)

    # Thống kê số lượng biên lai
    receipt_count = fields.Integer(string='Số lượng biên lai', compute='_compute_receipt_summary')
    receipt_count_display = fields.Char(string='Thông tin biên lai', compute='_compute_receipt_summary') # Dòng thông báo số lượng biên lai thu hồi

    # <<<< 6 BỘ TRƯỜNG TƯƠNG ỨNG TỐI ĐA 6 TAB BIÊN LAI THU HỒI XE (Mỗi nhóm chung người trả + ngày/giờ + địa điểm sẽ đổ vào 1 tab)
    # Tab Biên lai 1
    receipt_1_visible = fields.Boolean(default=False) # Cờ bật/tắt hiển thị Tab 1 trên giao diện XML
    receipt_1_name = fields.Char(string='Tên biên lai 1', default='Biên lai thu hồi 1')
    receipt_1_receipt_id = fields.Many2one('rental.return.receipt', string='Biên lai hiện tại 1') # Nếu nhóm này đã từng xuất biên lai thu hồi thì trỏ vào biên lai cũ để ghi đè
    receipt_1_state = fields.Selection(related='receipt_1_receipt_id.state', string='Trạng thái biên lai 1', readonly=True)
    receipt_1_customer_id = fields.Many2one('res.partner', string='Khách hàng trả xe')
    receipt_1_customer_phone = fields.Char(string='Số điện thoại')
    receipt_1_return_time = fields.Char(string='Giờ thu hồi xe')
    receipt_1_return_date = fields.Date(string='Ngày thu hồi xe')
    receipt_1_return_location = fields.Char(string='Địa điểm thu hồi xe', default='Tại cửa hàng')
    receipt_1_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_1_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_1_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_1_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_1_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_1_return_visual_note = fields.Text(string='Ghi chú ngoại quan chung', default='Ngoại quan bình thường, không trầy xước phát sinh.')
    receipt_1_vehicle_ids = fields.One2many(
        'rental.return.receipt.wizard.vehicle',
        'wizard_receipt_1_id',
        string='Xe biên lai 1'
    )

    # Tab Biên lai 2
    receipt_2_visible = fields.Boolean(default=False)
    receipt_2_name = fields.Char(string='Tên biên lai 2', default='Biên lai thu hồi 2')
    receipt_2_receipt_id = fields.Many2one('rental.return.receipt', string='Biên lai hiện tại 2')
    receipt_2_state = fields.Selection(related='receipt_2_receipt_id.state', string='Trạng thái biên lai 2', readonly=True)
    receipt_2_customer_id = fields.Many2one('res.partner', string='Khách hàng trả xe')
    receipt_2_customer_phone = fields.Char(string='Số điện thoại')
    receipt_2_return_time = fields.Char(string='Giờ thu hồi xe')
    receipt_2_return_date = fields.Date(string='Ngày thu hồi xe')
    receipt_2_return_location = fields.Char(string='Địa điểm thu hồi xe', default='Tại cửa hàng')
    receipt_2_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_2_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_2_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_2_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_2_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_2_return_visual_note = fields.Text(string='Ghi chú ngoại quan chung', default='Ngoại quan bình thường, không trầy xước phát sinh.')
    receipt_2_vehicle_ids = fields.One2many(
        'rental.return.receipt.wizard.vehicle',
        'wizard_receipt_2_id',
        string='Xe biên lai 2'
    )

    # Tab Biên lai 3
    receipt_3_visible = fields.Boolean(default=False)
    receipt_3_name = fields.Char(string='Tên biên lai 3', default='Biên lai thu hồi 3')
    receipt_3_receipt_id = fields.Many2one('rental.return.receipt', string='Biên lai hiện tại 3')
    receipt_3_state = fields.Selection(related='receipt_3_receipt_id.state', string='Trạng thái biên lai 3', readonly=True)
    receipt_3_customer_id = fields.Many2one('res.partner', string='Khách hàng trả xe')
    receipt_3_customer_phone = fields.Char(string='Số điện thoại')
    receipt_3_return_time = fields.Char(string='Giờ thu hồi xe')
    receipt_3_return_date = fields.Date(string='Ngày thu hồi xe')
    receipt_3_return_location = fields.Char(string='Địa điểm thu hồi xe', default='Tại cửa hàng')
    receipt_3_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_3_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_3_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_3_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_3_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_3_return_visual_note = fields.Text(string='Ghi chú ngoại quan chung', default='Ngoại quan bình thường, không trầy xước phát sinh.')
    receipt_3_vehicle_ids = fields.One2many(
        'rental.return.receipt.wizard.vehicle',
        'wizard_receipt_3_id',
        string='Xe biên lai 3'
    )

    # Tab Biên lai 4
    receipt_4_visible = fields.Boolean(default=False)
    receipt_4_name = fields.Char(string='Tên biên lai 4', default='Biên lai thu hồi 4')
    receipt_4_receipt_id = fields.Many2one('rental.return.receipt', string='Biên lai hiện tại 4')
    receipt_4_state = fields.Selection(related='receipt_4_receipt_id.state', string='Trạng thái biên lai 4', readonly=True)
    receipt_4_customer_id = fields.Many2one('res.partner', string='Khách hàng trả xe')
    receipt_4_customer_phone = fields.Char(string='Số điện thoại')
    receipt_4_return_time = fields.Char(string='Giờ thu hồi xe')
    receipt_4_return_date = fields.Date(string='Ngày thu hồi xe')
    receipt_4_return_location = fields.Char(string='Địa điểm thu hồi xe', default='Tại cửa hàng')
    receipt_4_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_4_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_4_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_4_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_4_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_4_return_visual_note = fields.Text(string='Ghi chú ngoại quan chung', default='Ngoại quan bình thường, không trầy xước phát sinh.')
    receipt_4_vehicle_ids = fields.One2many(
        'rental.return.receipt.wizard.vehicle',
        'wizard_receipt_4_id',
        string='Xe biên lai 4'
    )

    # Tab Biên lai 5
    receipt_5_visible = fields.Boolean(default=False)
    receipt_5_name = fields.Char(string='Tên biên lai 5', default='Biên lai thu hồi 5')
    receipt_5_receipt_id = fields.Many2one('rental.return.receipt', string='Biên lai hiện tại 5')
    receipt_5_state = fields.Selection(related='receipt_5_receipt_id.state', string='Trạng thái biên lai 5', readonly=True)
    receipt_5_customer_id = fields.Many2one('res.partner', string='Khách hàng trả xe')
    receipt_5_customer_phone = fields.Char(string='Số điện thoại')
    receipt_5_return_time = fields.Char(string='Giờ thu hồi xe')
    receipt_5_return_date = fields.Date(string='Ngày thu hồi xe')
    receipt_5_return_location = fields.Char(string='Địa điểm thu hồi xe', default='Tại cửa hàng')
    receipt_5_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_5_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_5_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_5_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_5_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_5_return_visual_note = fields.Text(string='Ghi chú ngoại quan chung', default='Ngoại quan bình thường, không trầy xước phát sinh.')
    receipt_5_vehicle_ids = fields.One2many(
        'rental.return.receipt.wizard.vehicle',
        'wizard_receipt_5_id',
        string='Xe biên lai 5'
    )

    # Tab Biên lai 6
    receipt_6_visible = fields.Boolean(default=False)
    receipt_6_name = fields.Char(string='Tên biên lai 6', default='Biên lai thu hồi 6')
    receipt_6_receipt_id = fields.Many2one('rental.return.receipt', string='Biên lai hiện tại 6')
    receipt_6_state = fields.Selection(related='receipt_6_receipt_id.state', string='Trạng thái biên lai 6', readonly=True)
    receipt_6_customer_id = fields.Many2one('res.partner', string='Khách hàng trả xe')
    receipt_6_customer_phone = fields.Char(string='Số điện thoại')
    receipt_6_return_time = fields.Char(string='Giờ thu hồi xe')
    receipt_6_return_date = fields.Date(string='Ngày thu hồi xe')
    receipt_6_return_location = fields.Char(string='Địa điểm thu hồi xe', default='Tại cửa hàng')
    receipt_6_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_6_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_6_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_6_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_6_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_6_return_visual_note = fields.Text(string='Ghi chú ngoại quan chung', default='Ngoại quan bình thường, không trầy xước phát sinh.')
    receipt_6_vehicle_ids = fields.One2many(
        'rental.return.receipt.wizard.vehicle',
        'wizard_receipt_6_id',
        string='Xe biên lai 6'
    )

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # TÍNH TỔNG SỐ TAB BIÊN LAI THU HỒI ĐANG BẬT VÀ CÂU THÔNG BÁO TÓM TẮT
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    @api.depends(
        'receipt_1_visible', 'receipt_2_visible', 'receipt_3_visible',
        'receipt_4_visible', 'receipt_5_visible', 'receipt_6_visible'
    )
    def _compute_receipt_summary(self):
        for rec in self:
            count = sum(1 for i in range(1, 7) if getattr(rec, f'receipt_{i}_visible')) # Đếm có bao nhiêu tab biên lai thu hồi đang hiện
            rec.receipt_count = count
            rec.receipt_count_display = f'Phiếu có {count} biên lai thu hồi xe.' if count else ''

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # 6 HÀM ONCHANGE: TỰ ĐỘNG ĐIỀN SĐT KHI ĐỔI NGƯỜI TRẢ XE TRÊN TỪNG TAB (1 -> 6)
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    @api.onchange('receipt_1_customer_id')
    def _onchange_receipt_1_customer_id(self):
        if self.receipt_1_customer_id:
            self.receipt_1_customer_phone = self.receipt_1_customer_id.phone or self.receipt_1_customer_id.mobile or ''

    @api.onchange('receipt_2_customer_id')
    def _onchange_receipt_2_customer_id(self):
        if self.receipt_2_customer_id:
            self.receipt_2_customer_phone = self.receipt_2_customer_id.phone or self.receipt_2_customer_id.mobile or ''

    @api.onchange('receipt_3_customer_id')
    def _onchange_receipt_3_customer_id(self):
        if self.receipt_3_customer_id:
            self.receipt_3_customer_phone = self.receipt_3_customer_id.phone or self.receipt_3_customer_id.mobile or ''

    @api.onchange('receipt_4_customer_id')
    def _onchange_receipt_4_customer_id(self):
        if self.receipt_4_customer_id:
            self.receipt_4_customer_phone = self.receipt_4_customer_id.phone or self.receipt_4_customer_id.mobile or ''

    @api.onchange('receipt_5_customer_id')
    def _onchange_receipt_5_customer_id(self):
        if self.receipt_5_customer_id:
            self.receipt_5_customer_phone = self.receipt_5_customer_id.phone or self.receipt_5_customer_id.mobile or ''

    @api.onchange('receipt_6_customer_id')
    def _onchange_receipt_6_customer_id(self):
        if self.receipt_6_customer_id:
            self.receipt_6_customer_phone = self.receipt_6_customer_id.phone or self.receipt_6_customer_id.mobile or ''

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # HÀM CỐT LÕI: LƯU / GHI ĐÈ BIÊN LAI THU HỒI TỪ CÁC TAB & ĐỒNG BỘ XUỐNG DÒNG XE
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def _save_receipts(self):
        """Xử lý tạo mới hoặc ghi đè biên lai thu hồi cho từng nhóm"""
        self.ensure_one()

        active_indices = [i for i in range(1, 7) if getattr(self, f'receipt_{i}_visible')] # Lấy danh sách số thứ tự các tab đang bật
        if not active_indices:
            raise UserError('Không có biên lai thu hồi nào để xuất!')

        all_vehicle_details = self.env['rental.operation.ticket.vehicle'] # Gom toàn bộ dòng xe có mặt trên các tab đang bật
        for i in active_indices:
            vlines = getattr(self, f'receipt_{i}_vehicle_ids')
            all_vehicle_details |= vlines.mapped('vehicle_detail_id')

        if not all_vehicle_details:
            raise UserError('Danh sách xe thu hồi không được để trống!')

        # <<<< 1. Cập nhật tình trạng ngoại quan thu hồi riêng cho từng chiếc xe (bỏ qua xe của biên lai đã thu hồi hoàn tất)
        for i in active_indices:
            rec_id = getattr(self, f'receipt_{i}_receipt_id')
            if rec_id and rec_id.state == 'returned': # Biên lai đã thu hồi hoàn tất thì đóng băng, không sửa
                continue
            vlines = getattr(self, f'receipt_{i}_vehicle_ids')
            for vline in vlines:
                if vline.vehicle_detail_id and vline.vehicle_detail_id.status != 'returned':
                    note = (vline.return_visual_note or '').strip()
                    vline.vehicle_detail_id.write({ # Ghi ghi chú ngoại quan khi nhận lại xuống model rental.operation.ticket.vehicle
                        'return_visual_note': note or 'Xe hoàn trả đầy đủ, ngoại quan bình thường, không trầy xước phát sinh.'
                    })

        created_receipts = self.env['rental.return.receipt'] # Tập hợp biên lai thu hồi đã tạo/cập nhật để trả về cho hàm in PDF
        # Danh sách tất cả biên lai chưa thu hồi thành công của ticket để ghi đè hoặc dọn dẹp
        candidate_receipts = self.ticket_id.return_receipt_ids.filtered(lambda r: r.state != 'returned')
        used_receipt_ids = set() # Tránh 2 tab ghi đè trùng vào cùng 1 biên lai

        # <<<< 2. Xử lý tạo mới hoặc ghi đè biên lai cho từng nhóm (mỗi tab = 1 biên lai thu hồi)
        for i in active_indices:
            vlines = getattr(self, f'receipt_{i}_vehicle_ids')
            grp_vehicles = vlines.mapped('vehicle_detail_id')
            if not grp_vehicles:
                continue

            # Chỉ xử lý các xe chưa thu hồi thành công (status != 'returned')
            # Trừ xe và biên lai đã thu hồi thành công ('returned')
            uncompleted_vehicles = grp_vehicles.filtered(lambda v: v.status != 'returned')
            if not uncompleted_vehicles:
                # Nếu nhóm toàn xe đã thu hồi thành công, giữ nguyên biên lai hiện có (nếu có)
                existing_receipt = getattr(self, f'receipt_{i}_receipt_id') or grp_vehicles.mapped('return_receipt_id')[:1]
                if existing_receipt:
                    created_receipts |= existing_receipt
                grp_vehicles.write({'is_selected': False})
                continue

            # Đọc dữ liệu từ các trường của tab thứ i (max(0, ...) để chặn số lượng phụ kiện bị âm)
            cust = getattr(self, f'receipt_{i}_customer_id') or self.ticket_id.customer_id
            cust_phone = getattr(self, f'receipt_{i}_customer_phone') or (cust.phone or cust.mobile or '')
            ret_time = getattr(self, f'receipt_{i}_return_time') or False
            ret_date = getattr(self, f'receipt_{i}_return_date') or False
            ret_loc = getattr(self, f'receipt_{i}_return_location') or 'Tại cửa hàng'
            q_helmet = max(0, getattr(self, f'receipt_{i}_qty_helmet'))
            q_raincoat = max(0, getattr(self, f'receipt_{i}_qty_raincoat'))
            q_phone_holder = max(0, getattr(self, f'receipt_{i}_qty_phone_holder'))
            q_charger = max(0, getattr(self, f'receipt_{i}_qty_charger'))
            vis_note = getattr(self, f'receipt_{i}_return_visual_note') or 'Ngoại quan bình thường, không trầy xước phát sinh.'

            receipt_vals = {
                'ticket_id': self.ticket_id.id,
                'customer_id': cust.id,
                'customer_phone': cust_phone,
                'return_time': ret_time or False,
                'return_date': ret_date or False,
                'return_location': ret_loc,
                'vehicle_ids': [(6, 0, uncompleted_vehicles.ids)], # (6, 0, ids): thay thế toàn bộ danh sách xe của biên lai bằng nhóm mới
                'qty_helmet': q_helmet,
                'qty_raincoat': q_raincoat,
                'qty_phone_holder': q_phone_holder,
                'qty_charger': q_charger,
                'return_visual_note': vis_note,
            }

            # <<<< Tìm biên lai chưa thu hồi thành công để ghi đè (theo 3 mức ưu tiên để tái sử dụng mã BLTH cũ, tránh sinh rác)
            existing_receipt = getattr(self, f'receipt_{i}_receipt_id') or False
            if existing_receipt and (existing_receipt.state == 'returned' or existing_receipt.id in used_receipt_ids):
                existing_receipt = False

            # Ưu tiên 1: Biên lai của xe trong nhóm chưa thu hồi thành công
            if not existing_receipt:
                for vl in uncompleted_vehicles:
                    if vl.return_receipt_id and vl.return_receipt_id in candidate_receipts and vl.return_receipt_id.id not in used_receipt_ids:
                        existing_receipt = vl.return_receipt_id
                        break

            # Ưu tiên 2: Khớp địa điểm và thời gian thu hồi
            if not existing_receipt:
                for cr in candidate_receipts:
                    if cr.id not in used_receipt_ids and cr.customer_id.id == cust.id:
                        if (cr.return_location or '').strip() == (ret_loc or '').strip() and (cr.return_time or '').strip() == (ret_time or '').strip():
                            existing_receipt = cr
                            break

            # Ưu tiên 3: Bất kỳ biên lai chưa thu hồi thành công nào còn lại
            if not existing_receipt:
                for cr in candidate_receipts:
                    if cr.id not in used_receipt_ids:
                        existing_receipt = cr
                        break

            if existing_receipt: # Có biên lai cũ chưa thu hồi -> ghi đè cập nhật
                existing_receipt.write(receipt_vals)
                receipt = existing_receipt
            else: # Không có biên lai cũ -> tạo mới biên lai thu hồi ở trạng thái chờ thu hồi ('pending')
                receipt_vals['state'] = 'pending'
                receipt = self.env['rental.return.receipt'].create(receipt_vals)

            used_receipt_ids.add(receipt.id)
            created_receipts |= receipt

            # <<<< 3. Gắn biên lai thu hồi vào từng dòng xe con và đồng bộ lại giờ/địa điểm thu hồi (nếu sửa trên wizard)
            for veh in uncompleted_vehicles:
                v_vals = {
                    'return_receipt_id': receipt.id,
                    'return_receipt_issued': True, # Đánh dấu xe đã được xuất biên lai thu hồi
                    'return_receipt_printed_at': fields.Datetime.now(), # Lưu thời điểm xuất biên lai thu hồi
                    'is_selected': False,
                }
                if ret_time and hasattr(veh, 'return_time') and veh.return_time != ret_time:
                    v_vals['return_time'] = ret_time
                    v_vals['is_custom_return_time'] = True # Bật cờ tùy chỉnh riêng để không bị ghi đè chung
                if ret_loc and veh.return_location != ret_loc:
                    v_vals['return_location'] = ret_loc
                    v_vals['is_custom_return_location'] = True
                veh.write(v_vals)

        # <<<< 4. Dọn dẹp các biên lai chưa thu hồi thành công bị dư thừa do gộp nhóm xe
        unused_pending_receipts = candidate_receipts.filtered(
            lambda r: r.id not in created_receipts.ids and not (r.vehicle_ids - all_vehicle_details)
        )
        if unused_pending_receipts:
            unused_pending_receipts.write({'vehicle_ids': [(5, 0, 0)]}) # (5, 0, 0): gỡ liên kết toàn bộ xe trước khi xóa
            unused_pending_receipts.unlink()

        if not created_receipts:
            raise UserError('Không có biên lai thu hồi nào được tạo hoặc cập nhật!')

        return created_receipts
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # 2 NÚT BẤM TRÊN POPUP: CHỈ LƯU HOẶC LƯU KÈM IN PDF
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def action_confirm_only(self):
        """Cập nhật biên lai không in báo cáo PDF và đóng màn hình popup"""
        self._save_receipts()
        return {'type': 'ir.actions.act_window_close'}

    def action_confirm_and_print(self):
        """Cập nhật biên lai và xuất file báo cáo PDF"""
        created_receipts = self._save_receipts()
        # report_action: phương thức có sẵn của Odoo để gọi mẫu in XML => report/return_receipt_report.xml
        action = self.env.ref('motorbike_rental_operation.action_report_return_receipt').report_action(created_receipts)
        action['close_on_report_download'] = True # Tự động đóng popup ngay khi trình duyệt bắt đầu tải PDF
        return action
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# MODEL TẠM: CHI TIẾT TỪNG DÒNG XE HIỂN THỊ TRONG CÁC TAB CỦA WIZARD THU HỒI XE
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class RentalReturnReceiptWizardVehicle(models.TransientModel):
    _name = 'rental.return.receipt.wizard.vehicle'
    _description = 'Chi Tiết Xe Thu Hồi Trong Wizard'

    # Khóa liên kết từng tab biên lai (1 -> 6) để hiển thị danh sách xe riêng biệt trên từng tab
    wizard_id = fields.Many2one('rental.return.receipt.wizard', ondelete='cascade')
    wizard_receipt_1_id = fields.Many2one('rental.return.receipt.wizard', ondelete='cascade')
    wizard_receipt_2_id = fields.Many2one('rental.return.receipt.wizard', ondelete='cascade')
    wizard_receipt_3_id = fields.Many2one('rental.return.receipt.wizard', ondelete='cascade')
    wizard_receipt_4_id = fields.Many2one('rental.return.receipt.wizard', ondelete='cascade')
    wizard_receipt_5_id = fields.Many2one('rental.return.receipt.wizard', ondelete='cascade')
    wizard_receipt_6_id = fields.Many2one('rental.return.receipt.wizard', ondelete='cascade')

    vehicle_detail_id = fields.Many2one('rental.operation.ticket.vehicle', string='Dòng xe gốc', required=True) # Liên kết về dòng xe thật trên phiếu vận hành
    vehicle_id = fields.Many2one('fleet.vehicle', string='Xe', related='vehicle_detail_id.vehicle_id', readonly=True)
    license_plate = fields.Char(string='Biển số xe', related='vehicle_id.license_plate', readonly=True)
    return_time = fields.Char(string='Giờ thu hồi', related='vehicle_detail_id.return_time', readonly=True)
    return_location = fields.Char(string='Địa điểm thu hồi', related='vehicle_detail_id.return_location', readonly=True)
    return_visual_note = fields.Text( # Cho phép nhân viên ghi nhận tình trạng/trầy xước thực tế ngay khi nhận lại xe
        string='Tình trạng xe khi nhận lại',
        default='Xe hoàn trả đầy đủ, ngoại quan bình thường, không trầy xước phát sinh.'
    )

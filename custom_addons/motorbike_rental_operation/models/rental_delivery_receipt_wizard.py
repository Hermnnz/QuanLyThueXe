# -*- coding: utf-8 -*-
"""Wizard Xác nhận & Xuất Biên lai Giao xe (TransientModel).

- Cho phép nhân viên kiểm tra phụ kiện (mũ, áo mưa, giá đỡ ĐT, sạc), ghi chú ngoại quan
  và chia nhóm xe theo địa điểm/thời gian giao để tạo hoặc cập nhật Biên lai giao xe.
- Hỗ trợ xuất báo cáo PDF biên bản bàn giao ngay sau khi lưu biên lai.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# WIZARD KIỂM ĐẾM PHỤ KIỆN, NGOẠI QUAN & XUẤT BIÊN LAI GIAO XE (TỐI ĐA 6 TAB NHÓM XE)
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class RentalDeliveryReceiptWizard(models.TransientModel):
    _name = 'rental.delivery.receipt.wizard'
    _description = 'Xác Nhận & Xuất Biên Lai Giao Xe'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', required=True)
    customer_id = fields.Many2one('res.partner', string='Khách hàng', related='ticket_id.customer_id', readonly=True) # Tự lấy khách hàng từ phiếu vận hành
    customer_phone = fields.Char(string='Số điện thoại', related='ticket_id.customer_phone', readonly=True)

    # Thống kê số lượng biên lai
    receipt_count = fields.Integer(string='Số lượng biên lai', compute='_compute_receipt_summary')
    receipt_count_display = fields.Char(string='Thông tin biên lai', compute='_compute_receipt_summary') # Dòng thông báo tóm tắt hiển thị trên đầu popup

    # <<<< 6 BỘ TRƯỜNG TƯƠNG ỨNG TỐI ĐA 6 TAB BIÊN LAI GIAO XE (Mỗi nhóm chung người nhận + ngày/giờ + địa điểm sẽ đổ vào 1 tab)
    # Tab Biên lai 1
    receipt_1_visible = fields.Boolean(default=False) # Cờ bật/tắt hiển thị Tab 1 trên giao diện XML
    receipt_1_name = fields.Char(string='Tên biên lai 1', default='Biên lai 1')
    receipt_1_receipt_id = fields.Many2one('rental.delivery.receipt', string='Biên lai hiện tại 1') # Nếu nhóm này đã từng xuất biên lai thì trỏ vào biên lai cũ để ghi đè
    receipt_1_state = fields.Selection(related='receipt_1_receipt_id.state', string='Trạng thái biên lai 1', readonly=True)
    receipt_1_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_1_customer_phone = fields.Char(string='Số điện thoại')
    receipt_1_delivery_time = fields.Char(string='Giờ giao xe')
    receipt_1_delivery_date = fields.Date(string='Ngày giao xe')
    receipt_1_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_1_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_1_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_1_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_1_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_1_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_1_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_1_id',
        string='Xe biên lai 1'
    )

    # Tab Biên lai 2
    receipt_2_visible = fields.Boolean(default=False)
    receipt_2_name = fields.Char(string='Tên biên lai 2', default='Biên lai 2')
    receipt_2_receipt_id = fields.Many2one('rental.delivery.receipt', string='Biên lai hiện tại 2')
    receipt_2_state = fields.Selection(related='receipt_2_receipt_id.state', string='Trạng thái biên lai 2', readonly=True)
    receipt_2_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_2_customer_phone = fields.Char(string='Số điện thoại')
    receipt_2_delivery_time = fields.Char(string='Giờ giao xe')
    receipt_2_delivery_date = fields.Date(string='Ngày giao xe')
    receipt_2_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_2_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_2_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_2_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_2_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_2_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_2_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_2_id',
        string='Xe biên lai 2'
    )

    # Tab Biên lai 3
    receipt_3_visible = fields.Boolean(default=False)
    receipt_3_name = fields.Char(string='Tên biên lai 3', default='Biên lai 3')
    receipt_3_receipt_id = fields.Many2one('rental.delivery.receipt', string='Biên lai hiện tại 3')
    receipt_3_state = fields.Selection(related='receipt_3_receipt_id.state', string='Trạng thái biên lai 3', readonly=True)
    receipt_3_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_3_customer_phone = fields.Char(string='Số điện thoại')
    receipt_3_delivery_time = fields.Char(string='Giờ giao xe')
    receipt_3_delivery_date = fields.Date(string='Ngày giao xe')
    receipt_3_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_3_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_3_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_3_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_3_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_3_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_3_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_3_id',
        string='Xe biên lai 3'
    )

    # Tab Biên lai 4
    receipt_4_visible = fields.Boolean(default=False)
    receipt_4_name = fields.Char(string='Tên biên lai 4', default='Biên lai 4')
    receipt_4_receipt_id = fields.Many2one('rental.delivery.receipt', string='Biên lai hiện tại 4')
    receipt_4_state = fields.Selection(related='receipt_4_receipt_id.state', string='Trạng thái biên lai 4', readonly=True)
    receipt_4_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_4_customer_phone = fields.Char(string='Số điện thoại')
    receipt_4_delivery_time = fields.Char(string='Giờ giao xe')
    receipt_4_delivery_date = fields.Date(string='Ngày giao xe')
    receipt_4_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_4_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_4_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_4_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_4_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_4_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_4_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_4_id',
        string='Xe biên lai 4'
    )

    # Tab Biên lai 5
    receipt_5_visible = fields.Boolean(default=False)
    receipt_5_name = fields.Char(string='Tên biên lai 5', default='Biên lai 5')
    receipt_5_receipt_id = fields.Many2one('rental.delivery.receipt', string='Biên lai hiện tại 5')
    receipt_5_state = fields.Selection(related='receipt_5_receipt_id.state', string='Trạng thái biên lai 5', readonly=True)
    receipt_5_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_5_customer_phone = fields.Char(string='Số điện thoại')
    receipt_5_delivery_time = fields.Char(string='Giờ giao xe')
    receipt_5_delivery_date = fields.Date(string='Ngày giao xe')
    receipt_5_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_5_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_5_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_5_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_5_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_5_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_5_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_5_id',
        string='Xe biên lai 5'
    )

    # Tab Biên lai 6
    receipt_6_visible = fields.Boolean(default=False)
    receipt_6_name = fields.Char(string='Tên biên lai 6', default='Biên lai 6')
    receipt_6_receipt_id = fields.Many2one('rental.delivery.receipt', string='Biên lai hiện tại 6')
    receipt_6_state = fields.Selection(related='receipt_6_receipt_id.state', string='Trạng thái biên lai 6', readonly=True)
    receipt_6_customer_id = fields.Many2one('res.partner', string='Khách hàng nhận xe')
    receipt_6_customer_phone = fields.Char(string='Số điện thoại')
    receipt_6_delivery_time = fields.Char(string='Giờ giao xe')
    receipt_6_delivery_date = fields.Date(string='Ngày giao xe')
    receipt_6_delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')
    receipt_6_vehicle_count = fields.Integer(string='Số lượng xe', default=1)
    receipt_6_qty_helmet = fields.Integer(string='Mũ bảo hiểm (cái)', default=2)
    receipt_6_qty_raincoat = fields.Integer(string='Áo mưa (cái)', default=2)
    receipt_6_qty_phone_holder = fields.Integer(string='Giá đỡ ĐT (cái)', default=1)
    receipt_6_qty_charger = fields.Integer(string='Bộ sạc xe (bộ)', default=1)
    receipt_6_vehicle_ids = fields.One2many(
        'rental.delivery.receipt.wizard.vehicle',
        'wizard_receipt_6_id',
        string='Xe biên lai 6'
    )

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # TÍNH TỔNG SỐ TAB BIÊN LAI ĐANG BẬT VÀ CÂU THÔNG BÁO TÓM TẮT
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    @api.depends(
        'receipt_1_visible', 'receipt_2_visible', 'receipt_3_visible',
        'receipt_4_visible', 'receipt_5_visible', 'receipt_6_visible'
    )
    def _compute_receipt_summary(self):
        for rec in self:
            count = sum(1 for i in range(1, 7) if getattr(rec, f'receipt_{i}_visible')) # Đếm có bao nhiêu tab biên lai đang hiển thị (visible=True)
            rec.receipt_count = count
            if count == 1:
                rec.receipt_count_display = 'Phiếu có 1 biên lai giao xe cần xuất.'
            elif count > 1:
                rec.receipt_count_display = f'Phiếu có {count} biên lai giao xe cần xuất (theo nhóm Người nhận, Giờ và Địa điểm giao). Vui lòng kiểm tra ở từng tab bên dưới.'
            else:
                rec.receipt_count_display = 'Không có biên lai nào cần xuất.'

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # 6 HÀM ONCHANGE: TỰ ĐỘNG ĐIỀN SĐT KHI ĐỔI NGƯỜI NHẬN XE TRÊN TỪNG TAB (1 -> 6)
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
    # HÀM CỐT LÕI: LƯU / GHI ĐÈ BIÊN LAI GIAO XE TỪ CÁC TAB & ĐỒNG BỘ XUỐNG DÒNG XE
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def _save_receipts(self):
        """Xác nhận thông tin: Ghi mới hoặc ghi đè lên biên lai cũ tương ứng từng nhóm"""
        self.ensure_one()

        active_indices = [i for i in range(1, 7) if getattr(self, f'receipt_{i}_visible')] # Lấy danh sách số thứ tự các tab đang bật
        if not active_indices:
            raise UserError('Không có biên lai nào để lưu!')

        all_vehicle_details = self.env['rental.operation.ticket.vehicle'] # Gom tất cả dòng xe có mặt trên các tab đang bật
        for i in active_indices:
            vlines = getattr(self, f'receipt_{i}_vehicle_ids')
            all_vehicle_details |= vlines.mapped('vehicle_detail_id')

        if not all_vehicle_details:
            raise UserError('Danh sách xe giao không được để trống!')

        # <<<< 1. Cập nhật tình trạng ngoại quan ban đầu riêng cho từng chiếc xe (bỏ qua xe của biên lai đã giao thành công)
        for i in active_indices:
            rec_id = getattr(self, f'receipt_{i}_receipt_id')
            if rec_id and rec_id.state == 'delivered': # Biên lai đã giao thành công thì đóng băng, không ghi đè ngoại quan
                continue
            vlines = getattr(self, f'receipt_{i}_vehicle_ids')
            for vline in vlines:
                if vline.vehicle_detail_id and vline.vehicle_detail_id.status in ('waiting', 'delivering'):
                    note = (vline.delivery_visual_note or '').strip()
                    if not note and vline.vehicle_id: # Nếu người dùng xóa trống ghi chú thì lấy lại ngoại quan từ Fleet
                        note = vline.vehicle_detail_id._get_vehicle_exterior_condition(vline.vehicle_id)
                    note = note or 'Ngoại quan của xe không có vấn đề'
                    vline.vehicle_detail_id.write({'delivery_visual_note': note}) # Ghi xuống model rental.operation.ticket.vehicle

        created_receipts = self.env['rental.delivery.receipt'] # Tập hợp các biên lai được tạo mới hoặc cập nhật để trả về cho hàm in PDF
        # Danh sách tất cả biên lai chưa giao thành công của ticket để ghi đè hoặc dọn dẹp
        candidate_receipts = self.ticket_id.receipt_ids.filtered(lambda r: r.state != 'delivered')
        used_receipt_ids = set() # Đánh dấu ID biên lai đã được gán cho 1 tab để tránh 2 tab ghi đè trùng lên cùng 1 biên lai

        # <<<< 2. Xử lý tạo mới hoặc ghi đè biên lai cho từng nhóm (mỗi tab = 1 biên lai)
        for i in active_indices:
            vlines = getattr(self, f'receipt_{i}_vehicle_ids')
            grp_vehicles = vlines.mapped('vehicle_detail_id')
            if not grp_vehicles:
                continue

            # Chỉ xử lý các xe chưa giao thành công ('waiting', 'delivering')
            # Trừ xe và biên lai đã giao thành công ('delivered')
            uncompleted_vehicles = grp_vehicles.filtered(lambda v: v.status in ('waiting', 'delivering'))
            if not uncompleted_vehicles:
                # Nếu nhóm toàn xe đã giao thành công, giữ nguyên biên lai hiện có (nếu có)
                existing_receipt = getattr(self, f'receipt_{i}_receipt_id') or grp_vehicles.mapped('delivery_receipt_id')[:1]
                if existing_receipt:
                    created_receipts |= existing_receipt
                grp_vehicles.write({'is_selected': False})
                continue

            # Đọc dữ liệu từ các trường của tab thứ i (max(0, ...) để chặn số lượng phụ kiện bị âm)
            cust = getattr(self, f'receipt_{i}_customer_id') or self.ticket_id.customer_id
            cust_phone = getattr(self, f'receipt_{i}_customer_phone') or (cust.phone or cust.mobile or '')
            deliv_time = getattr(self, f'receipt_{i}_delivery_time') or False
            deliv_date = getattr(self, f'receipt_{i}_delivery_date') or False
            deliv_loc = getattr(self, f'receipt_{i}_delivery_location') or 'Tại cửa hàng'
            q_helmet = max(0, getattr(self, f'receipt_{i}_qty_helmet'))
            q_raincoat = max(0, getattr(self, f'receipt_{i}_qty_raincoat'))
            q_phone_holder = max(0, getattr(self, f'receipt_{i}_qty_phone_holder'))
            q_charger = max(0, getattr(self, f'receipt_{i}_qty_charger'))

            receipt_vals = {
                'ticket_id': self.ticket_id.id,
                'customer_id': cust.id,
                'customer_phone': cust_phone,
                'delivery_time': deliv_time or False,
                'delivery_date': deliv_date or False,
                'delivery_location': deliv_loc,
                'vehicle_ids': [(6, 0, uncompleted_vehicles.ids)], # (6, 0, ids): thay thế toàn bộ danh sách xe của biên lai bằng nhóm mới
                'qty_helmet': q_helmet,
                'qty_raincoat': q_raincoat,
                'qty_phone_holder': q_phone_holder,
                'qty_charger': q_charger,
            }

            # <<<< Tìm biên lai chưa giao thành công để ghi đè (theo 3 mức ưu tiên để tái sử dụng mã BLGX cũ, tránh sinh rác)
            existing_receipt = getattr(self, f'receipt_{i}_receipt_id') or False
            if existing_receipt and (existing_receipt.state == 'delivered' or existing_receipt.id in used_receipt_ids):
                existing_receipt = False

            # Ưu tiên 1: Biên lai của xe trong nhóm chưa giao thành công
            if not existing_receipt:
                for vl in uncompleted_vehicles:
                    if vl.delivery_receipt_id and vl.delivery_receipt_id in candidate_receipts and vl.delivery_receipt_id.id not in used_receipt_ids:
                        existing_receipt = vl.delivery_receipt_id
                        break

            # Ưu tiên 2: Khớp địa điểm và thời gian giao
            if not existing_receipt:
                for cr in candidate_receipts:
                    if cr.id not in used_receipt_ids and cr.customer_id.id == cust.id:
                        if (cr.delivery_location or '').strip() == (deliv_loc or '').strip() and (cr.delivery_time or '').strip() == (deliv_time or '').strip():
                            existing_receipt = cr
                            break

            # Ưu tiên 3: Bất kỳ biên lai chưa giao thành công nào còn lại
            if not existing_receipt:
                for cr in candidate_receipts:
                    if cr.id not in used_receipt_ids:
                        existing_receipt = cr
                        break

            if existing_receipt: # Có biên lai cũ chưa giao -> ghi đè cập nhật
                existing_receipt.write(receipt_vals)
                receipt = existing_receipt
            else: # Không có biên lai cũ -> tạo mới biên lai giao xe ở trạng thái chờ giao ('pending')
                receipt_vals['state'] = 'pending'
                receipt = self.env['rental.delivery.receipt'].create(receipt_vals)

            used_receipt_ids.add(receipt.id)
            created_receipts |= receipt

            # <<<< 3. Gắn biên lai vào từng dòng xe con và đồng bộ lại giờ/địa điểm giao (nếu sửa trên wizard)
            for veh in uncompleted_vehicles:
                v_vals = {
                    'delivery_receipt_id': receipt.id,
                    'delivery_receipt_issued': True, # Đánh dấu xe đã được xuất biên lai giao
                    'receipt_printed_at': fields.Datetime.now(), # Lưu thời điểm xuất biên lai
                    'is_selected': False,
                }
                if deliv_time and veh.delivery_time != deliv_time:
                    v_vals['delivery_time'] = deliv_time
                    v_vals['is_custom_delivery_time'] = True # Bật cờ tùy chỉnh riêng để không bị ghi đè chung
                if deliv_loc and veh.delivery_location != deliv_loc:
                    v_vals['delivery_location'] = deliv_loc
                    v_vals['is_custom_delivery_location'] = True
                veh.write(v_vals)

        # <<<< 4. Dọn dẹp các biên lai chưa giao thành công bị dư thừa do gộp nhóm xe
        unused_pending_receipts = candidate_receipts.filtered(
            lambda r: r.id not in created_receipts.ids and not (r.vehicle_ids - all_vehicle_details)
        )
        if unused_pending_receipts:
            unused_pending_receipts.write({'vehicle_ids': [(5, 0, 0)]}) # (5, 0, 0): gỡ liên kết toàn bộ xe trước khi xóa
            unused_pending_receipts.unlink()

        if not created_receipts:
            raise UserError('Không có biên lai nào được tạo hoặc cập nhật!')

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
        # report_action: phương thức có sẵn của Odoo để gọi mẫu in XML => report/delivery_receipt_report.xml
        action = self.env.ref('motorbike_rental_operation.action_report_delivery_receipt').report_action(created_receipts)
        action['close_on_report_download'] = True # Tự động đóng popup ngay khi trình duyệt bắt đầu tải PDF
        return action
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# MODEL TẠM: CHI TIẾT TỪNG DÒNG XE HIỂN THỊ TRONG CÁC TAB CỦA WIZARD GIAO XE
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
class RentalDeliveryReceiptWizardVehicle(models.TransientModel):
    _name = 'rental.delivery.receipt.wizard.vehicle'
    _description = 'Chi Tiết Xe Bàn Giao Trong Wizard'

    # Khóa liên kết từng tab biên lai (1 -> 6) để hiển thị danh sách xe riêng biệt trên từng tab
    wizard_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_1_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_2_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_3_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_4_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_5_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')
    wizard_receipt_6_id = fields.Many2one('rental.delivery.receipt.wizard', ondelete='cascade')

    vehicle_detail_id = fields.Many2one('rental.operation.ticket.vehicle', string='Dòng xe gốc', required=True) # Liên kết về dòng xe thật trên phiếu vận hành
    vehicle_id = fields.Many2one('fleet.vehicle', string='Xe', related='vehicle_detail_id.vehicle_id', readonly=True)
    license_plate = fields.Char(string='Biển số xe', related='vehicle_id.license_plate', readonly=True)
    delivery_time = fields.Char(string='Giờ giao', related='vehicle_detail_id.delivery_time', readonly=True)
    delivery_location = fields.Char(string='Địa điểm giao', related='vehicle_detail_id.delivery_location', readonly=True)
    delivery_visual_note = fields.Text( # Cho phép nhân viên sửa ghi chú ngoại quan ngay trên popup trước khi in
        string='Tình trạng ngoại quan ban đầu',
        required=True,
        default='Ngoại quan của xe không có vấn đề'
    )


# Model tạm phiên bản cũ (giữ lại để tương thích ngược nếu DB cũ còn tham chiếu)
class RentalDeliveryReceiptWizardGroup(models.TransientModel):
    _name = 'rental.delivery.receipt.wizard.group'
    _description = 'Nhóm Biên Lai Giao Xe (Legacy)'
    name = fields.Char()

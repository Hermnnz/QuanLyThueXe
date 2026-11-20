# -*- coding: utf-8 -*-
"""Model Chi tiết Xe trong Phiếu Vận Hành (Operation Ticket Vehicle) & mở rộng FleetVehicle.

- Trạng thái từng xe (status):
  + Chưa giao (waiting) -> Đang giao xe (delivering) -> Đang cho thuê (renting) -> Đã thu hồi (returned).
- Tự động đồng bộ 2 chiều:
  + Khi giao xe thành công (renting): xe bên Fleet -> renting, Hợp đồng -> Đang thuê (in_progress).
  + Khi thu hồi xe (returned): xe bên Fleet -> Chờ kiểm tra (pending_inspection) & technical_ready = False.
  + Tự động đồng bộ trạng thái Biên lai giao/nhận và kiểm tra hoàn tất Phiếu đổi xe (Xe A trả + Xe B giao).
- Bảo vệ dữ liệu: chặn thêm/xóa xe ngoài hợp đồng (trừ luồng Đổi xe có cờ allow_vehicle_exchange),
  chặn sửa địa điểm/giờ giao nhận khi xe đã giao hoặc đã thu hồi.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    def write(self, vals):
        res = super().write(vals)
        if 'description' in vals:
            TicketVehicle = self.env['rental.operation.ticket.vehicle']
            for vehicle in self:
                new_note = TicketVehicle._get_vehicle_exterior_condition(vehicle)
                pending_lines = TicketVehicle.search([
                    ('vehicle_id', '=', vehicle.id),
                    ('status', 'in', ('waiting', 'delivering')),
                ])
                if pending_lines:
                    pending_lines.write({'delivery_visual_note': new_note})
        return res


class RentalOperationTicketVehicle (models.Model):
    _name = 'rental.operation.ticket.vehicle'
    _description = 'Chi tiết Xe Vận Hành'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', ondelete='cascade')
    rental_order_ref = fields.Char(string='Thuộc Đơn thuê', related='ticket_id.rental_order_ref', readonly=True)

    # Ô tick chọn phục vụ thao tác hàng loạt
    is_selected = fields.Boolean(string='Chọn', default=False)


    @api.onchange('is_selected')
    def _onchange_is_selected(self):
        if self.ticket_id:
            #Kiểm tra có phiếu vận hành đã hoàn tất / hợp đồng của phiếu vận hành đó hoàn tất
            if self.ticket_id.state == 'done' or (self.ticket_id.contract_id and self.ticket_id.contract_id.state == 'done'):
                self.is_selected = False
                self.ticket_id.has_selected_vehicles = False
                return
            # Nếu có một xe True sẽ trả về True để hiện btn Cập nhật thời gian/địa điểm
            self.ticket_id.has_selected_vehicles = any(self.ticket_id.vehicle_detail_ids.mapped('is_selected'))

    # Tiền tệ kế thừa từ phiếu tổng
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        related='ticket_id.currency_id',
        store=True,
        readonly=True,
    )

    vehicle_id = fields.Many2one('fleet.vehicle', string='Xe', required=True)
    subfleet = fields.Boolean(string='Xe thay thế', default=False, readonly=True)
    license_plate = fields.Char(string='Biển số xe', related='vehicle_id.license_plate', readonly=True)
    vehicle_price = fields.Monetary(string='Giá tiền xe', default=0.0, currency_field='currency_id')
    # Thông tin vận chuyển - Mặc định lấy từ địa điểm chung của hợp đồng/phiếu
    delivery_location = fields.Char(string='Vị trí giao', default='Tại cửa hàng')
    delivery_date = fields.Date(string='Ngày giao xe')
    return_date = fields.Date(string='Ngày thu hồi xe')
    return_location = fields.Char(string='Vị trí thu hồi', default='Tại cửa hàng')
    delivery_time = fields.Char(string='Giờ giao xe', default=False, help='Thời gian dự kiến giao xe (VD: 08:30)')
    return_time = fields.Char(string='Giờ thu hồi xe', default=False, help='Thời gian dự kiến thu hồi xe (VD: 18:00)')
    # Đánh dấu người dùng đã chỉnh riêng địa điểm / thời gian (không bị ghi đè khi đổi giá trị chung)
    is_custom_delivery_location = fields.Boolean(string='Chỉnh địa điểm giao riêng', default=False)
    is_custom_return_location = fields.Boolean(string='Chỉnh địa điểm thu hồi riêng', default=False)
    is_custom_delivery_time = fields.Boolean(string='Chỉnh giờ giao riêng', default=False)
    is_custom_return_time = fields.Boolean(string='Chỉnh giờ thu hồi riêng', default=False)
    is_custom_delivery_date = fields.Boolean(string='Chỉnh ngày giao riêng', default=False)
    is_custom_return_date = fields.Boolean(string='Chỉnh ngày thu hồi riêng', default=False)


# <<<<<<<<<<<<<<<<< CÁC HÀM ĐIỀU KIỆN CHUYỂN TRẠNG THÁI XE <<<<<<<<<<<<<<<<<<<<
    @api.onchange('delivery_location')
    def _onchange_delivery_location(self):
        if self.status in ('renting', 'returned'):
            name = self._get_vehicle_label()
            raise UserError(f'Xe {name} đã được bàn giao (hoặc đã thu hồi), không được phép chỉnh sửa Địa chỉ giao xe!')
        if self.ticket_id and self.delivery_location != self.ticket_id.quick_delivery_location:
            self.is_custom_delivery_location = True

    @api.onchange('return_location')
    def _onchange_return_location(self):
        if self.status == 'returned':
            name = self._get_vehicle_label()
            raise UserError(f'Xe {name} đã được thu hồi hoàn tất, không được phép chỉnh sửa Địa chỉ thu hồi xe!')
        if self.ticket_id and self.return_location != self.ticket_id.quick_return_location: # NẾU THAY ĐỔI VỊ TRÍ KHÁC VỊ TRÍ MẶC ĐỊNH THÌ BẬT ĐÃ CHỈNH SỬA RIÊNG
            self.is_custom_return_location = True

    @api.onchange('delivery_time')
    def _onchange_delivery_time(self):
        if self.status in ('renting', 'returned'):
            name = self._get_vehicle_label()
            raise UserError(f'Xe {name} đã được bàn giao (hoặc đã thu hồi), không được phép chỉnh sửa Giờ giao xe!')
        if self.ticket_id and hasattr(self.ticket_id, 'quick_delivery_time') and self.delivery_time != self.ticket_id.quick_delivery_time:
            self.is_custom_delivery_time = True

    @api.onchange('return_time')
    def _onchange_return_time(self):
        if self.status == 'returned':
            name = self._get_vehicle_label()
            raise UserError(f'Xe {name} đã được thu hồi hoàn tất, không được phép chỉnh sửa Giờ thu hồi xe!')
        if self.ticket_id and hasattr(self.ticket_id, 'quick_return_time') and self.return_time != self.ticket_id.quick_return_time:
            self.is_custom_return_time = True

    @api.onchange('delivery_date')
    def _onchange_delivery_date(self):
        if self.status in ('renting', 'returned'):
            name = self._get_vehicle_label()
            raise UserError(f'Xe {name} đã được bàn giao (hoặc đã thu hồi), không được phép chỉnh sửa Ngày giao xe!')
        self.is_custom_delivery_date = True

    @api.onchange('return_date')
    def _onchange_return_date(self):
        if self.status == 'returned':
            name = self._get_vehicle_label()
            raise UserError(f'Xe {name} đã được thu hồi hoàn tất, không được phép chỉnh sửa Ngày thu hồi xe!')
        self.is_custom_return_date = True
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# <<<<<<<<<<<<<<<<< GIAO THU HỒI XE <<<<<<<<<<<<<<<<<<<<
    # Thông tin Biên lai bàn giao xe & Phụ kiện đi kèm (lưu vết phục vụ khi Thu hồi xe)
    delivery_receipt_id = fields.Many2one('rental.delivery.receipt', string='Biên lai giao xe', readonly=True)
    delivery_receipt_issued = fields.Boolean(string='Đã xuất biên lai', default=False, readonly=True) #ĐỂ NẾU CÓ SỬA BIÊN LAI THÌ SẼ CẬP NHẬT BIÊN LAI CŨ CHỨ KHÔNG TẠO THÊM BIÊN LAI
    receipt_printed_at = fields.Datetime(string='Thời điểm xuất biên lai', readonly=True)
    # Tình trạng ngoại quan lúc giao xe
    delivery_visual_note = fields.Text(
        string='Ngoại quan khi giao',
        default='Ngoại quan của xe không có vấn đề'
    )

    # Thông tin Biên lai thu hồi xe & Tình trạng khi trả
    return_receipt_id = fields.Many2one('rental.return.receipt', string='Biên lai thu hồi xe', readonly=True)
    return_receipt_issued = fields.Boolean(string='Đã xuất biên lai thu hồi', default=False, readonly=True)
    return_receipt_printed_at = fields.Datetime(string='Thời điểm xuất biên lai thu hồi', readonly=True)
    return_visual_note = fields.Text(
        string='Ngoại quan khi thu hồi',
        default='Xe hoàn trả đầy đủ, ngoại quan bình thường, không trầy xước phát sinh.'
    )

    # 4 món phụ kiện đi kèm cố định (mặc định 2 mũ, 2 áo mưa, 1 giá đt, 1 sạc/xe)
    qty_helmet = fields.Integer(string='Mũ bảo hiểm', default=2)
    qty_raincoat = fields.Integer(string='Áo mưa', default=2)
    qty_phone_holder = fields.Integer(string='Giá đỡ điện thoại', default=1)
    qty_charger = fields.Integer(string='Bộ sạc xe', default=1)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# <<<<<<<<<<<<<<<<<<<<<<<< LẤY TÌNH TRẠNG NGOẠI QUAN CỦA XE <<<<<<<<<<<<<<<<<<
    @api.model #LẤY TỪ VEHICLE ==> BẢN GIAO XE (Chạy khi 2 hàm dưới gọi)
    def _get_vehicle_exterior_condition(self, vehicle): 
        """
        Lấy thông tin ngoại quan xe từ trường description trên fleet.vehicle (tab 'Mô tả tình trạng').
        Nếu không có giá trị gì, mặc định là: 'Ngoại quan của xe không có vấn đề'
        """
        default_val = 'Ngoại quan của xe không có vấn đề'
        if not vehicle:
            return default_val

        if isinstance(vehicle, int): # Kiểm tra kiểu dữ liệu của vehicle, nếu là id thì cần chuyển vehicle sang 
            vehicle = self.env['fleet.vehicle'].browse(vehicle) # Là nguyên một bản ghi dữ liệu
        if not vehicle.exists(): # Kiểm tra bản ghi có tồn tại trong bảng fleet.vehicle không
            return default_val

        # Đọc trực tiếp trường description từ fleet.vehicle
        raw_val = vehicle.sudo().description
        if not raw_val:
            return default_val

        # Xử lý làm sạch thẻ HTML nếu có
        if isinstance(raw_val, str) and ('<' in raw_val and '>' in raw_val):
            cleaned = html2plaintext(raw_val).strip() # Bóc tách thẻ HTML
        else:
            cleaned = str(raw_val).strip()

        return cleaned or default_val

    
    def _get_display_visual_note(self):
        """Lấy tình trạng ngoại quan chuẩn xác nhất để hiển thị và xuất báo cáo PDF"""
        self.ensure_one()
        note = (self.delivery_visual_note or '').strip()
        if note:
            return note

        if self.vehicle_id: #Nếu cột ngoại quan không có thì dùng hàm gọi ngoại quan từ bang vehicle
            return self._get_vehicle_exterior_condition(self.vehicle_id) 

        return 'Ngoại quan của xe không có vấn đề'

    @api.onchange('vehicle_id') # Chạy khi thay đổi trên giao diện
    def _onchange_vehicle_id_exterior(self):
        if self.vehicle_id:
            self.delivery_visual_note = self._get_vehicle_exterior_condition(self.vehicle_id)

    @api.model_create_multi   # Hàm lấy tình trạng ngoại quan và kiểm tra khi thêm xe
    def create(self, vals_list):
        for vals in vals_list:
            # 1. Tự động lấy ghi chú ngoại quan từ xe nếu chưa nhập
            if vals.get('vehicle_id') and not (vals.get('delivery_visual_note') or '').strip():
                vals['delivery_visual_note'] = self._get_vehicle_exterior_condition(vals['vehicle_id'])

            # 2. Kiểm tra điều kiện bảo mật trên Phiếu vận hành cha
            ticket_id = vals.get('ticket_id')
            if ticket_id:
                ticket = self.env['rental.operation.ticket'].browse(ticket_id)
                # Chặn thêm xe nếu Phiếu vận hành đã bị hủy
                if ticket.state == 'contract_cancelled':
                    raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không thể thêm xe!'))

                # Xe ngoài hợp đồng chỉ được tạo qua nút Đổi xe; xe gốc chỉ nạp khi lập phiếu
                if not self.env.context.get('allow_vehicle_exchange') and (
                    ticket.state != 'waiting'
                    or vals.get('vehicle_id') not in ticket.contract_id.line_ids.mapped('vehicle_id').ids
                ):
                    raise UserError(_('Chỉ được thêm xe thay thế bằng nút Đổi xe.'))

        # 3. Gọi super để Odoo chính thức lưu các dòng xe vào cơ sở dữ liệu
        records = super(RentalOperationTicketVehicle, self).create(vals_list)

        # 4. Xử lý logic hậu tạo mới (Post-create)
        for rec in records:
            if rec.status in ('delivering', 'renting'):
                rec._check_fleet_delivery_eligibility()
            if rec.status == 'renting':
                rec._sync_contract_in_progress()
                if rec.vehicle_id:
                    rec.vehicle_id.sudo().write({'operational_status': 'renting'})

        return records

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # Lịch trình & Thời gian thực tế (cho phép chỉnh sửa)
    date_checkout = fields.Datetime(string='Thời gian giao dự kiến')
    actual_delivery_date = fields.Datetime(string='Thời gian giao thực tế')
    date_checkin = fields.Datetime(string='Thời gian thu hồi dự kiến')
    actual_return_date = fields.Datetime(string='Thời gian thu hồi thực tế')

    status = fields.Selection([
        ('waiting', 'Chưa giao'),
        ('delivering', 'Đang giao xe'),
        ('renting', 'Đang cho thuê'),
        ('returned', 'Đã thu hồi')
    ], string='Trạng thái Xe', default='waiting')

    def _get_vehicle_label(self): # Hàm lấy tên hiển thị của xe
        self.ensure_one()
        if self.vehicle_id:
            return self.vehicle_id.display_name or self.vehicle_id.name or 'N/A'
        return 'không xác định'
    
# <<<<<<<<<<<<<<<<<<<<<<< KIỂM TRA TRƯỚC KHI GIAO XE <<<<<<<<<<<<<<<<<<<
    # Bởi vì khi chọn xe B để đem đổi, đã khóa trạng thái xe B, 
    # nên nếu muốn giao xe B cần có hàm này để pass kiểm tra ở hàm giao xe
    def _is_confirmed_exchange_vehicle_b(self):  
        """Kiểm tra xe có phải là xe đem đi đổi (xe B) trong bảng Đổi xe hay không.
        Đặc biệt: Bắt buộc phải nằm ở bản ghi Xác nhận (confirmed),
        không được nằm ở bản ghi Hủy (cancelled) hoặc Đã thực hiện / Hoàn thành (done).
        """
        self.ensure_one()
        vehicle = self.vehicle_id
        if not vehicle:
            return False

        exchanges = self.env['rental.vehicle.exchange']
        if self.ticket_id and self.ticket_id.vehicle_exchange_ids:
            # Kiểm tra xem có phải là xe đem đi đổi không
            exchanges = self.ticket_id.vehicle_exchange_ids.filtered(lambda e: e.vehicle_b_id == vehicle)

        # Kiểm tra dưới DB
        if not exchanges:
            contract = self.ticket_id.contract_id if self.ticket_id else False
            domain = [('vehicle_b_id', '=', vehicle.id)]
            if contract:
                domain.append(('ticket_id.contract_id', '=', contract.id)) # Kiểm tra đúng hợp đồng hiện tại
            exchanges = self.env['rental.vehicle.exchange'].sudo().search(domain)
        if not exchanges:
            return False

        # Đặc biệt: Bắt buộc phải nằm ở bản ghi Xác nhận (confirmed), không được nằm trong Hủy (cancelled) hoặc Đã thực hiện (done)
        return bool(exchanges.filtered(lambda e: e.status == 'confirmed'))

    # HÀM KIỂM TRA CÁC ĐIỀU KIỆN TRƯỚC KHI BẤM "BẮT ĐẦU GIAO XE"
    def _check_fleet_delivery_eligibility(self):
        """Kiểm tra xe có đủ điều kiện từ Fleet để giao hay không trước khi giao xe cho khách"""
        for rec in self:
            vehicle = rec.vehicle_id
            if not vehicle:
                continue

            # Kiểm tra trạng thái hợp đồng: Không được giao xe khi hợp đồng ở trạng thái Nháp
            contract = rec.ticket_id.contract_id if rec.ticket_id else False
            if contract and contract.state == 'draft':
                raise UserError(_('Không thể giao xe khi hợp đồng đang ở trạng thái Nháp! Vui lòng xác nhận hợp đồng trước.'))

            # ******===> Kiểm tra xe có phải là xe đem đi đổi trong bảng Đổi xe đang Xác nhận (confirmed)
            # Nếu nằm ở trường hợp này thì vẫn cho phép chuyển trạng thái giao (bỏ qua điều kiện kiểm tra kỹ thuật / Fleet)
            if rec._is_confirmed_exchange_vehicle_b():
                continue # Nếu là xe đem đi đổi thì bỏ qua kiểm tra

            # 1. Trạng thái vận hành phải là 'available' nếu xe chưa xuất phát đi giao ('waiting')
            if rec.status == 'waiting' and vehicle.operational_status != 'available':
                name = rec._get_vehicle_label()
                status_labels = dict(vehicle._fields['operational_status'].selection) if hasattr(vehicle, '_fields') and 'operational_status' in vehicle._fields else {}
                current_st = status_labels.get(vehicle.operational_status, vehicle.operational_status)
                raise ValidationError(_(
                    'Xe "%(name)s" không ở trạng thái sẵn sàng để bàn giao (Trạng thái hiện tại của xe: "%(status)s").'
                ) % {'name': name, 'status': current_st})

            # 2. Lấy khoảng thời gian thuê để kiểm tra với Fleet
            start = rec.date_checkout or (contract.start_date if contract else False)
            end = rec.date_checkin or (contract.end_date if contract else False)

            if not start or not end or start >= end:
                now = fields.Datetime.now()
                start = now
                end = fields.Datetime.add(now, hours=1)

            # 3. Sử dụng trực tiếp hàm kiểm tra của Fleet: check_fleet_availability
            if hasattr(vehicle, 'check_fleet_availability'):
                availability = vehicle.check_fleet_availability(start, end)
                if availability and not availability[0].get('fleet_ok'):
                    reasons = availability[0].get('reasons', []) # Lấy index 0 vì chỉ kiểm tra 1 chiếc xe, lấy danh sách lý do
                    reason_map = {
                        'rental_blocked': _('Xe đang bị khóa thuê (Lý do: %s)') % (vehicle.block_reason or _('Không có lý do cụ thể')),
                        'not_technical_ready': _('Xe chưa đạt tiêu chuẩn kỹ thuật (technical_ready = False)'),
                        'blocking_maintenance': _('Xe đang có lịch bảo dưỡng/sửa chữa chưa hoàn tất'),
                        'not_electric_motorbike': _('Xe không phải là xe máy điện hợp lệ'),
                        'archived': _('Xe đã bị lưu trữ (archived)'),
                        'inactive_catalog': _('Dòng xe hoặc hãng xe đang bị tạm ngưng'),
                    }
                    details = [str(reason_map.get(r, r)) for r in reasons]  # Map mã lý do với reason_map để trả về tiếng Việt
                    name = rec._get_vehicle_label()   
                    raise ValidationError(_(
                        'Xe "%(name)s" chưa đủ điều kiện Fleet để giao:\n- %(reasons)s'
                    ) % {
                        'name': name,
                        'reasons': '\n- '.join(details),
                    })
            # Kiểm tra trực tiếp 2 cột boolean trong bảng vehicle
            elif getattr(vehicle, 'rental_blocked', False) or not getattr(vehicle, 'technical_ready', True):
                name = rec._get_vehicle_label()
                reasons = []
                if getattr(vehicle, 'rental_blocked', False):
                    reasons.append(_('Xe đang bị khóa thuê (Lý do: %s)') % (getattr(vehicle, 'block_reason', '') or _('Không có lý do cụ thể'))) 
                if not getattr(vehicle, 'technical_ready', True):
                    reasons.append(_('Xe chưa đạt tiêu chuẩn kỹ thuật'))
                raise ValidationError(_(
                    'Xe "%(name)s" chưa đủ điều kiện Fleet để giao:\n- %(reasons)s'
                ) % {
                    'name': name,
                    'reasons': '\n- '.join(reasons),
                })
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# <<<<<<<<<<<<<<<<<<<<<< HÀM BẮT ĐẦU GIAO XE <<<<<<<<<<<<<<
    def action_start_delivery(self):
        """Bắt đầu giao xe cho từng chiếc - Cập nhật xe bên Bắc sang Đang cho thuê (renting)"""
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa!'))

        # 1. Kích hoạt bộ kiểm tra điều kiện kỹ thuật với Fleet vừa học ở trên
        self._check_fleet_delivery_eligibility()

        for rec in self:
            name = rec._get_vehicle_label()
            if rec.status == 'returned':
                raise UserError(f'Xe {name} đã được thu hồi!')
            if rec.status == 'renting':
                raise UserError(f'Xe {name} đã được giao!')

            # 2. Đổi trạng thái dòng xe sang Đang đi giao của bảng Chi tiết vận hành xe
            # Xác nhận xe B đang đi giao, nhưng không xác nhận xe B đã được giao vì hoạt động đổi xe chưa hoàn tất
            rec.write({
                'status': 'delivering',
                'is_selected': False,
            })
            # 3. Cập nhật sang bảng Fleet: đánh dấu xe đang chạy trên đường
            if rec.vehicle_id and not rec.subfleet: # Loại trừ xe B vì xe A phải được thu hồi trước thì xe B mới được chuyển sang đang thuê
                rec.vehicle_id.sudo().write({'operational_status': 'renting'})

        # 4. Tự động đồng bộ trạng thái của Biên lai giao xe
        self._sync_delivery_receipt_state()

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< XÁC NHẬN ĐÃ GIAO XE THÀNH CÔNG <<<<<<<<<<<<<<

    # Kiểm tra xem xe A đã được thu hồi hay chưa trước khi cho phép xác nhận đang đi giao xe B
    def _require_a_returned_before_b_delivery(self):
        """Không giao xe thay thế khi chưa có xác nhận thu hồi xe cũ."""
        for line_b in self.filtered('subfleet'): # Kiểm tra xem có phải xe đem đi đổi không
            exchange = line_b.ticket_id.vehicle_exchange_ids.filtered(
                lambda item: item.ticket_line_b_id == line_b and item.status == 'confirmed'
            )[:1] # Tìm các phiếu đổi xe của xe B đã được xác nhận (Lấy bản ghi đầu tiên để tránh lỗi singleton)
            if not exchange:
                raise UserError(_('Không tìm thấy phiếu đổi xe đang thực hiện.'))

            line_a = line_b.ticket_id.vehicle_detail_ids.filtered(
                lambda item: item.vehicle_id == exchange.vehicle_a_id
            )[:1] # Lấy thông tin xe A
            if not line_a or line_a.status != 'returned': # Nếu không có xe A, hoặc xe A chưa được thu hồi thì báo lỗi
                raise UserError(_('Phải xác nhận biên lai thu hồi xe A trước khi giao xe B.'))

    # XÁC NHẬN ĐÃ GIAO XE THÀNH CÔNG
    def action_confirm_delivery(self):
        """Xác nhận đã bàn giao xe thành công cho khách - Xe bên Bắc ở trạng thái Đang cho thuê (renting)"""
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa!'))

        # 1. Nếu là xe đổi B, bắt buộc xe cũ A phải được thu hồi trước
        self._require_a_returned_before_b_delivery()

        # 2. Kiểm tra điều kiện xe bên Fleet
        self._check_fleet_delivery_eligibility() 

        for rec in self:
            name = rec._get_vehicle_label()
            if rec.status == 'returned':
                raise UserError(f'Xe {name} đã được thu hồi!')
            if rec.status == 'renting':
                raise UserError(f'Xe {name} đã được giao!')

            # 3. Chuyển trạng thái dòng xe sang "Đang cho thuê" và ghi nhận giờ giao thực tế
            vals = {
                'status': 'renting', 
                'is_selected': False,
            }

            if not rec.actual_delivery_date:
                vals['actual_delivery_date'] = fields.Datetime.now() # Lấy giờ giao thực tế

            rec.write(vals) # Ghi dữ liệu vào DB

            # 4. Ghi nhận giờ giao thực tế lên Phiếu vận hành tổng (nếu phiếu chưa có)
            if rec.ticket_id and not rec.ticket_id.actual_delivery_date:
                rec.ticket_id.actual_delivery_date = fields.Datetime.now()

            # 5. Đồng bộ Hợp đồng sang "Đang thuê" (in_progress)
            rec._sync_contract_in_progress()

            # 6. Chuyển trạng thái xe vật lý bên Fleet sang "Đang thuê" (renting)
            if rec.vehicle_id:
                rec.vehicle_id.sudo().write({'operational_status': 'renting'}) # Lúc này xe B mới chuyển sang đang thuê

        # 7. Đồng bộ biên lai và kích hoạt kiểm tra hoàn tất đổi xe
        self._sync_delivery_receipt_state()  # Cập nhật biên lai giao xe
        self._sync_return_receipt_state()  # Cập nhật biên lai thu hồi xe
        
        # Cập nhật xe B vào chi tiết hợp đồng khi xe A
        # đã thu hồi thành công và xe B giao thành công.
        # Cập nhật trạng thái đổi xe hoàn thành.
        self._check_and_sync_vehicle_exchanges() 

    # Cập nhật vào hợp đồng ngay khi việc đổi xe thành công (Xe A xác nhận đã thu hồi và Xe B xác nhận đã giao thành công)
    # Cập nhật xe B vào chi tiết hợp đồng và xác nhận đổi xe thành công
    def _check_and_sync_vehicle_exchanges(self):
        """Tự động kiểm tra và cập nhật hoàn thành cho bản ghi đổi xe:
        Khi Xe B đã giao thành công (status in ('renting', 'returned')).
        Đồng thời chuyển xe A sang 'maintenance'.
        """
        tickets = self.mapped('ticket_id')
        for ticket in tickets:
            active_exchanges = ticket.vehicle_exchange_ids.filtered(lambda e: e.status == 'confirmed')
            for ex in active_exchanges:
                line_a = ticket.vehicle_detail_ids.filtered(lambda l: l.vehicle_id == ex.vehicle_a_id)
                line_b = ticket.vehicle_detail_ids.filtered(lambda l: l.vehicle_id == ex.vehicle_b_id)

                is_b_delivered = bool(line_b and all(l.status in ('renting', 'returned') for l in line_b))

                if is_b_delivered and line_a and all(l.status == 'returned' for l in line_a):
                    if not ex.contract_line_b_id:
                        original = ticket.contract_id.line_ids.filtered(
                            lambda line: line.vehicle_id == ex.vehicle_a_id
                        )[:1]
                        if not original:
                            raise UserError(_('Không tìm thấy xe A trong hợp đồng.'))
                        ex.contract_line_b_id = self.env['rental.contract.line'].sudo().with_context(
                            allow_vehicle_exchange=True
                        ).create({
                            'contract_id': ticket.contract_id.id,
                            'vehicle_id': ex.vehicle_b_id.id,
                            'vehicle_type_id': original.vehicle_type_id.id,
                            'daily_rate': original.daily_rate,
                            'subfleet': True,
                            'return_deadline': original.return_deadline,  # Xe B kế thừa hạn trả của A, không lấy hạn muộn nhất của xe khác.
                            'billing_line_id': (original.billing_line_id or original).id,  # A→B→C vẫn chỉ tính tiền vào cùng một dòng thuê gốc.
                            'notes': _('Đổi xe: thay cho %s') % ex.vehicle_a_id.display_name,
                        })
                    ex.write({'status': 'done'}) # Xác nhận đổi xe thành công


    def _sync_delivery_receipt_state(self):
        """Đồng bộ trạng thái biên lai giao xe khi xe chuyển trạng thái"""
        receipts = self.mapped('delivery_receipt_id') | self.mapped('ticket_id.receipt_ids') # Dùng toán tử | để gộp 2 tập hợp: tìm tập hợp các phiếu giao của xe, sau đó gộp chúng lại
        if receipts:
            receipts._compute_state() # Cập nhật trạng thái các biên lai giao xe

    def _sync_return_receipt_state(self):
        """Đồng bộ trạng thái biên lai thu hồi xe khi xe chuyển trạng thái"""
        receipts = self.mapped('return_receipt_id') | self.mapped('ticket_id.return_receipt_ids')
        if receipts:
            receipts._compute_state()

    def _sync_contract_in_progress(self):
        """Khi có xe trong bản ghi giao xe được giao ('renting'), chuyển hợp đồng sang Đang thuê ('in_progress')"""
        for rec in self:
            contract = rec.ticket_id.contract_id if rec.ticket_id else False
            if contract and contract.state == 'confirmed':
                contract.sudo().write({'state': 'in_progress'}) # Chuyển hợp đồng từ confirmed sang đang thuê (in_progress)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<< XÁC NHẬN THU HỒI XE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    def action_confirm_return(self):
        """Xác nhận thu hồi xe từ khách - Mặc định xe bên Bắc chuyển sang Chờ kiểm tra (pending_inspection)"""

        for rec in self: # Nếu hợp đồng đã bị hủy thì bị khóa
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa!'))
        
        for rec in self:  # Kiểm tra trạng thái của xe
            name = rec._get_vehicle_label()
            if rec.status in ('waiting', 'delivering'):
                raise UserError(f'Xe {name} chưa được bàn giao!')
            if rec.status == 'returned':
                raise UserError(f'Xe {name} đã được thu hồi!')

            vals = { # Tạo tập giá trị cần thay đổi
                'status': 'returned',
                'is_selected': False,
            }
            
            if not rec.actual_return_date:
                vals['actual_return_date'] = fields.Datetime.now()
            rec.write(vals) # Ghi giá trị thay đổi vào DB

            # Khi tất cả xe đã về kho thì cập nhật thời gian hoàn thành vận hành
            if rec.ticket_id: 
                all_returned = all(v.status == 'returned' for v in rec.ticket_id.vehicle_detail_ids)
                if all_returned:
                    if not rec.ticket_id.actual_return_date:
                        rec.ticket_id.actual_return_date = fields.Datetime.now()
            # Đẩy dữ liệu xe sang Fleet là cần kiểm tra (pending_inspection)
            if rec.vehicle_id:
                rec.vehicle_id.sudo().write({
                    'operational_status': 'pending_inspection',
                    'technical_ready': False,
                })

        # Đổi trạng thái các biên lai
        self._sync_delivery_receipt_state()  # Cập nhật biên lai giao xe
        self._sync_return_receipt_state()  # Cập nhật biên lai thu hồi xe
        
        # Cập nhật xe B vào chi tiết hợp đồng khi xe A
        # đã thu hồi thành công và xe B giao thành công.
        # Cập nhật trạng thái đổi xe hoàn thành.
        self._check_and_sync_vehicle_exchanges() 
# >>>>>>>>>>>>>>>>>>>>>>> XÁC NHẬN ĐÃ THU HỒI XE XONG >>>>>>>>>>>

# <<<<<<<<<<<<<<<<<<<< HÀM GHI ĐÈ WRITE - KIỂM TRA KHI CẬP NHẬT DỮ LIỆU <<<<<<<<<<<<<<<<<
    def write(self, vals):
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không được phép chỉnh sửa chi tiết xe!'))

        if 'status' in vals and vals['status'] in ('delivering', 'renting'):
            self._check_fleet_delivery_eligibility() # Kiểm tra điều kiện Fleet trước khi chuyển sang Đang giao / Đang thuê

        # Chặn thay đổi địa chỉ & thời gian khi đã giao hoặc thu hồi xe thành công
        if 'delivery_location' in vals:
            for rec in self:
                if rec.status in ('renting', 'returned') and vals['delivery_location'] != rec.delivery_location:
                    name = rec._get_vehicle_label()
                    raise UserError(f'Xe {name} đã được bàn giao cho khách (hoặc đã thu hồi), không được phép chỉnh sửa Địa chỉ giao xe!')
        if 'delivery_time' in vals:
            for rec in self:
                if rec.status in ('renting', 'returned') and vals['delivery_time'] != rec.delivery_time:
                    name = rec._get_vehicle_label()
                    raise UserError(f'Xe {name} đã được bàn giao cho khách (hoặc đã thu hồi), không được phép chỉnh sửa Giờ giao xe!')
        if 'return_location' in vals:
            for rec in self:
                if rec.status == 'returned' and vals['return_location'] != rec.return_location:
                    name = rec._get_vehicle_label()
                    raise UserError(f'Xe {name} đã được thu hồi hoàn tất, không được phép chỉnh sửa Địa chỉ thu hồi xe!')
        if 'return_time' in vals:
            for rec in self:
                if rec.status == 'returned' and vals['return_time'] != rec.return_time:
                    name = rec._get_vehicle_label()
                    raise UserError(f'Xe {name} đã được thu hồi hoàn tất, không được phép chỉnh sửa Giờ thu hồi xe!')
        # >>>>>>>>>>>>>>>

        # Gọi super().write để ghi dữ liệu vào DB
        # Quyền sửa dòng vận hành đã được kiểm tra trước khi đồng bộ trạng thái xe bằng quyền hệ thống.
        res = super(RentalOperationTicketVehicle, self).write(vals)

        # Đồng bộ trạng thái sang Fleet, Hợp đồng và Biên lai
        if 'status' in vals:
            for rec in self:
                if rec.vehicle_id:
                    if vals['status'] == 'renting' or (vals['status'] == 'delivering' and not rec.subfleet):
                        rec.vehicle_id.sudo().write({'operational_status': 'renting'})
                    elif vals['status'] == 'returned':
                        rec.vehicle_id.sudo().write({
                            'operational_status': 'pending_inspection', # Trạng thái xe sang Chờ kiểm tra
                            'technical_ready': False, # Reset điều kiện kỹ thuật về False
                        })

                # Khi xe ở trạng thái đã giao xe ('renting'), hợp đồng chuyển sang trạng thái Đang thuê ('in_progress')
                if vals['status'] == 'renting':
                    rec._sync_contract_in_progress()
            self._sync_delivery_receipt_state()
            self._sync_return_receipt_state()
        self._check_and_sync_vehicle_exchanges() # >>>>>>>>>>>>>>>


        if 'delivery_location' in vals or 'delivery_time' in vals:
            for rec in self:
                if rec.delivery_receipt_id and rec.delivery_receipt_id.state != 'delivered':
                    r_vals = {}
                    if 'delivery_location' in vals and vals['delivery_location']:
                        r_vals['delivery_location'] = vals['delivery_location']
                    if 'delivery_time' in vals:
                        r_vals['delivery_time'] = vals['delivery_time']
                    if r_vals:
                        rec.delivery_receipt_id.write(r_vals)

        if 'return_location' in vals or 'return_time' in vals:
            for rec in self:
                if rec.return_receipt_id and rec.return_receipt_id.state != 'returned':
                    r_vals = {}
                    if 'return_location' in vals and vals['return_location']:
                        r_vals['return_location'] = vals['return_location']
                    if 'return_time' in vals:
                        r_vals['return_time'] = vals['return_time']
                    if r_vals:
                        rec.return_receipt_id.write(r_vals)
        return res

    # <<<<<<<<<<< ĐƯA TRẠNG THÁI CÁC XE VỀ CHƯA GIAO
    def action_reset_waiting(self):
        """Khôi phục về trạng thái chưa giao"""
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa!'))
            rec.write({
                'status': 'waiting',
                'is_selected': False,
            })

    # <<<<<<<<<< CẤM XÓA CHI TIẾT XE VẬN HÀNH
    # Chỉ được xóa khi đổi xe ('allow_vehicle_exchange' được gắn cờ trong quy trình đổi xe)
    def unlink(self):
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không thể xóa chi tiết xe!'))
            if rec.ticket_id and not self.env.context.get('delete_ticket') and not self.env.context.get('allow_vehicle_exchange'):
                raise UserError('Không được phép xóa xe khỏi phiếu bàn giao! Danh sách xe được lấy theo hợp đồng thuê.')
        return super(RentalOperationTicketVehicle, self).unlink()
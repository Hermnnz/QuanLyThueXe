# -*- coding: utf-8 -*-
"""Model Nhật ký Sự cố & Hư hỏng trong quá trình vận hành (Incident Log).

- Trạng thái:
  + Đang thực hiện (processing): Sự cố mới ghi nhận, đang xử lý sửa chữa/bồi thường.
  + Hoàn tất (resolved): Đã giải quyết xong sự cố và chốt chi phí.
- Liên kết với Phiếu vận hành, Xe gặp sự cố và Bảng giá phụ phí (price_catalog).
- Tự động tính tổng tiền bồi thường và đồng bộ sang bộ phận tài chính/hợp đồng khi cần.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RentalIncidentLog(models.Model):
    _name = 'rental.operation.incident.log'
    _description = 'Nhật ký Sự cố & Hư hỏng'

    name = fields.Char(string='Mã sự cố', required=True, copy=False, readonly=True, default='Mới')

    ticket_id = fields.Many2one(
        'rental.operation.ticket', 
        string='Thuộc Phiếu Vận Hành', 
        ondelete='cascade',
        domain="[('state', '!=', 'contract_cancelled')]"
    )
    
    # Ô tick chọn phục vụ thao tác hàng loạt
    is_selected = fields.Boolean(string='Chọn', default=False)
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        related='ticket_id.currency_id',
        store=True,
        readonly=True,
    )
    price_catalog_id = fields.Many2one(
        'motorbike.rental.price.catalog',
        string='Loại sự cố / Bồi thường',
        domain="[('category', 'in', ('compensation', 'surcharge'))]",
    )
    quantity = fields.Integer(
        string='Số lượng / Số giờ',
        default=1,
    )
    unit = fields.Selection(
        related='price_catalog_id.unit',
        string='Đơn vị tính',
        readonly=True,
    )
    unit_price = fields.Monetary(
        string='Đơn giá',
        currency_field='currency_id',
    )
    penalty_amount = fields.Monetary(
        string='Tiền phạt / Bồi thường',
        currency_field='currency_id',
        compute='_compute_penalty_amount',
        store=True,
        readonly=False,
    )

    available_vehicle_ids = fields.Many2many( # Chứa danh sách xe có trong phiếu
        'fleet.vehicle',
        compute='_compute_available_vehicle_ids',
        string='Xe có trong phiếu'
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Xe gặp sự cố',
        required=True,
        domain="[('id', 'in', available_vehicle_ids)]"
    )

    date_reported = fields.Datetime(string='Ngày giờ ghi nhận', default=fields.Datetime.now)
    fault_party = fields.Selection([
        ('customer', 'Lỗi do Khách hàng'),
        ('vehicle', 'Lỗi do Xe / Công ty')
    ], string='Lỗi thuộc về', required=True, default='customer')
    
    damage_description = fields.Text(string='Mô tả chi tiết lỗi')
    needs_repair = fields.Boolean(string='Cần sửa chữa?', default=False)
    needs_repair_display = fields.Selection(
        [
            ('no', 'Không cần sửa chữa'),
            ('yes', 'Cần sửa chữa'),
        ],
        string='Cần sửa chữa?',
        default='no',
        compute='_compute_needs_repair_display',
        inverse='_inverse_needs_repair_display',
        store=True,
    )

    service_id = fields.Many2one(
        'fleet.vehicle.log.services',
        string='Hồ sơ sửa chữa (Fleet)',
        readonly=True,
        copy=False,
    )

    status = fields.Selection([
        ('processing', 'Đang thực hiện'),
        ('resolved', 'Hoàn tất')
    ], string='Trạng thái', default='processing')

    # ---------------------------------------------------------------------
    # CREATE_MULTI
    # ---------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            ticket_id = vals.get('ticket_id') # Lấy ID Phiếu vận hành (không phải Hợp đồng)
            if ticket_id: # Kiểm tra trạng thái Phiếu vận hành
                ticket = self.env['rental.operation.ticket'].browse(ticket_id)
                if ticket.state == 'contract_cancelled':
                    raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không thể tạo hoặc liên kết sự cố!'))
            if not vals.get('name') or vals.get('name') == 'Mới': # Kiểm tra nếu chưa có mã sự cố thì tự sinh mã từ sequence
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.operation.incident.log')
            if vals.get('price_catalog_id') and not vals.get('unit_price'): # Nếu cột đơn giá (unit_price) chưa có thì gọi sang bảng giá sự cố để lấy
                catalog = self.env['motorbike.rental.price.catalog'].browse(vals['price_catalog_id'])
                vals['unit_price'] = catalog.unit_price
            if 'quantity' not in vals: # Nếu không có số lượng thì mặc định là 1
                vals['quantity'] = 1
            if 'penalty_amount' not in vals:
                qty = vals.get('quantity') if vals.get('quantity') is not None else 1 # Chuẩn bị số lượng & đơn giá (tiền phạt sẽ do _compute_penalty_amount tính)
                price = vals.get('unit_price') or 0.0

            if 'needs_repair_display' in vals and 'needs_repair' not in vals:
                vals['needs_repair'] = (vals['needs_repair_display'] == 'yes')

        return super(RentalIncidentLog, self).create(vals_list)


    # ---------------------------------------------------------------------
    # WRITE
    # ---------------------------------------------------------------------
    def write(self, vals):
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không thể chỉnh sửa sự cố!'))

        if 'ticket_id' in vals and vals['ticket_id']: # Nếu đổi sang phiếu vận hành khác thì kiểm tra trạng thái hủy của phiếu mới đó
            new_ticket = self.env['rental.operation.ticket'].browse(vals['ticket_id'])
            if new_ticket.state == 'contract_cancelled':
                raise UserError(_('Không thể liên kết sự cố tới phiếu vận hành ở trạng thái "Hợp đồng bị hủy"!'))

        if 'needs_repair_display' in vals and 'needs_repair' not in vals:
            vals['needs_repair'] = (vals['needs_repair_display'] == 'yes')

        # <<<<< Nếu đã có hồ sơ sửa chữa bên Fleet (service_id), không cho phép đổi thành "Không cần sửa chữa"
        is_turning_off_repair = (
            ('needs_repair' in vals and not vals['needs_repair']) or
            ('needs_repair_display' in vals and vals['needs_repair_display'] == 'no')
        )

        if is_turning_off_repair:
            for rec in self:
                if rec.service_id:
                    raise UserError(_('Sự cố "%s" đã được đồng bộ sang hồ sơ bảo dưỡng & sửa chữa của Fleet, không thể chuyển thành "Không cần sửa chữa"!') % (rec.name or ''))

        return super(RentalIncidentLog, self).write(vals) # >>>>>>>>>>>>>>>>


    # ---------------------------------------------------------------------
    # CÁC HÀM CHẠY TỰ ĐỘNG VỀ ĐƠN GIÁ / TIỀN / LOẠI VI PHẠM
    # ---------------------------------------------------------------------
    # Hàm tính tổng tiền phạt khi thay đổi số lượng / đơn giá / loại vi phạm
    @api.depends('quantity', 'unit_price', 'price_catalog_id') # Chạy cả khi bấm Lưu trên giao diện lẫn khi thay đổi bằng code (lưu DB)
    def _compute_penalty_amount(self):
        for rec in self:
            qty = rec.quantity if rec.quantity is not None else 1
            price = rec.unit_price if rec.unit_price else (rec.price_catalog_id.unit_price if rec.price_catalog_id else 0.0)
            rec.penalty_amount = (qty or 0) * (price or 0.0)
    
    # Chạy ngay khi đổi hạng mục sự cố trên giao diện
    @api.onchange('price_catalog_id') # Giao diện (tức thì, chưa lưu DB)
    def _onchange_price_catalog_id(self):
        if self.price_catalog_id:
            self.unit_price = self.price_catalog_id.unit_price
            if not self.quantity or self.quantity <= 0:
                self.quantity = 1
            self.penalty_amount = (self.quantity or 1) * (self.unit_price or 0.0)
            if not self.damage_description:
                self.damage_description = self.price_catalog_id.name

    # Chạy ngay khi đổi số lượng hoặc đơn giá trên giao diện
    @api.onchange('quantity', 'unit_price') # Giao diện (tức thì, chưa lưu DB)
    def _onchange_quantity_price(self):
        qty = self.quantity if self.quantity is not None else 1
        price = self.unit_price if self.unit_price else 0.0
        self.penalty_amount = (qty or 0) * (price or 0.0)

    # ---------------------------------------------------------------------
    # HÀM CHẠY TỰ ĐỘNG LẤY DANH SÁCH XE TRONG CHI TIẾT PHIẾU VẬN HÀNH
    # ---------------------------------------------------------------------
    @api.depends('ticket_id', 'ticket_id.vehicle_detail_ids.vehicle_id') # Chạy lại khi thay đổi phiếu VH hoặc danh sách xe trong phiếu VH
    def _compute_available_vehicle_ids(self):
        for rec in self:
            if rec.ticket_id and rec.ticket_id.vehicle_detail_ids: # Kiểm tra có phiếu VH và có danh sách chi tiết xe trong phiếu VH
                rec.available_vehicle_ids = rec.ticket_id.vehicle_detail_ids.mapped('vehicle_id') # Rút trích các chiếc xe thật (fleet.vehicle) từ từng dòng chi tiết vận hành của phiếu này
            else:
                rec.available_vehicle_ids = self.env['fleet.vehicle'].search([]) # Nếu chưa chọn phiếu VH (hoặc phiếu chưa có xe) thì lấy tất cả xe trong kho

    # ---------------------------------------------------------------------
    # HÀM TỰ ĐỘNG CHỌN MẶC ĐỊNH XE NẾU PHIẾU CHỈ THUÊ 1 XE DUY NHẤT
    # ---------------------------------------------------------------------
    @api.onchange('ticket_id')
    def _onchange_ticket_id_default_vehicle(self):
        if self.ticket_id and self.ticket_id.vehicle_detail_ids:
            vehicles = self.ticket_id.vehicle_detail_ids.mapped('vehicle_id')
            if len(vehicles) == 1 and not self.vehicle_id:
                self.vehicle_id = vehicles[0]

    # ---------------------------------------------------------------------
    # HÀM KIỂM TRA VIỆC ĐỔI TỪ CẦN SỬA CHỮA THÀNH KHÔNG SỬA CHỮA TRÊN GIAO DIỆN
    # Chặn khi thay đổi ở giao diện, nếu qua API hay hàm thì chặn ở write
    # ===> Nếu tick nhầm thì chỉ thông báo lỗi và tiếp tục | Nếu chọn lưu thì báo lỗi và thoát ra
    # ---------------------------------------------------------------------
    @api.onchange('needs_repair_display')
    def _onchange_needs_repair_display(self):
        if self.service_id and self.needs_repair_display == 'no':
            self.needs_repair_display = 'yes'
            self.needs_repair = True
            return {
                'warning': {
                    'title': _('Cảnh báo'),
                    'message': _('Sự cố này đã được đồng bộ sang hồ sơ bảo dưỡng & sửa chữa của Fleet, không thể chuyển thành "Không cần sửa chữa"!')
                }
            }
        if self.needs_repair_display:
            self.needs_repair = (self.needs_repair_display == 'yes')

    # ---------------------------------------------------------------------
    # CỤM HÀM ĐỒNG BỘ 2 CHIỀU GIỮA needs_repair (Boolean) VÀ needs_repair_display (Selection)

    # - Khi tick đổi trạng thái Cần sửa / Không cần sửa trên giao diện:
    #   needs_repair thay đổi -> cập nhật needs_repair_display thành 'yes'/'no'

    # - Khi tải dữ liệu từ DB (Compute):
    #   Đọc needs_repair -> gán giá trị tương ứng cho needs_repair_display

    # - Khi lưu từ giao diện về DB (Inverse):
    #   Lấy giá trị 'yes'/'no' -> ghi ngược lại vào needs_repair (True/False)
    # ---------------------------------------------------------------------
    @api.onchange('needs_repair')
    def _onchange_needs_repair(self):
        self.needs_repair_display = 'yes' if self.needs_repair else 'no'

    @api.depends('needs_repair') #DB ==> GD
    def _compute_needs_repair_display(self):
        for rec in self:
            rec.needs_repair_display = 'yes' if rec.needs_repair else 'no'

    def _inverse_needs_repair_display(self): # GD ==> DB
        for rec in self:
            is_repair = (rec.needs_repair_display == 'yes')
            if rec.needs_repair != is_repair:
                rec.needs_repair = is_repair

    
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # HÀM ĐẨY DỮ LIỆU SANG VEHICLE KHI CÓ XE CẦN SỬA CHỮA
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    def _sync_to_fleet_service(self):
        """Khi phiếu sự cố có 'Cần sửa chữa?', tự động đổ dữ liệu sang bảng Bảo dưỡng & Sửa chữa của Fleet"""
        if self.env.context.get('skip_sync_fleet'): # Bỏ qua việc đồng bộ sang sửa chữa (chống lặp vô tận)
            return

        Service = self.env['fleet.vehicle.log.services'].sudo() # Khởi tạo đối tượng model Sửa chữa xe (Fleet) với quyền quản trị

        for rec in self.with_context(skip_sync_fleet=True): # with_context(skip_sync_fleet=True) ==> Gắn cờ context để tránh kích hoạt đồng bộ đệ quy lặp vô tận
            if rec.needs_repair and not rec.service_id and rec.vehicle_id:
                cust_name = False
                cust_phone = False
                if rec.ticket_id and rec.ticket_id.customer_id: # Nếu tìm được thông tin khách hàng từ phiếu vận hành thì lấy tên và số điện thoại
                    cust_name = rec.ticket_id.customer_id.name
                    cust_phone = rec.ticket_id.customer_id.phone or rec.ticket_id.customer_id.mobile

                desc = rec.damage_description or (rec.price_catalog_id.name if rec.price_catalog_id else '') # Lấy nội dung hư hỏng hoặc tên danh mục vi phạm
                full_desc = f"[{rec.name}] {desc}" if desc else f"Sự cố {rec.name}" # Ghép mã sự cố vào tiêu đề mô tả

                # Lấy loại dịch vụ sửa chữa (service_type_electric_maintenance là XML ID của bản ghi 'Bảo dưỡng xe điện' trong module Fleet)
                service_type = self.env.ref('motorbike_fleet_management.service_type_electric_maintenance', raise_if_not_found=False)

                if not service_type:
                    service_type = self.env['fleet.service.type'].sudo().search([], limit=1) # Dự phòng: Lấy tạm loại dịch vụ đầu tiên nếu không tìm thấy XML ID

                service_vals = {
                    'vehicle_id': rec.vehicle_id.id,
                    'maintenance_type': 'corrective', # 'corrective': Sửa chữa khắc phục hư hỏng phát sinh (phân biệt với bảo dưỡng định kỳ 'preventive' trong fleet_service)
                    'description': full_desc,
                    'customer_name': cust_name,
                    'customer_phone': cust_phone,
                    'amount': rec.penalty_amount or 0.0,
                    'date': rec.date_reported.date() if rec.date_reported else fields.Date.context_today(self),
                    'state': 'new',
                    'blocks_rental': True,
                    'notes': f"Tự động tạo từ Sự cố {rec.name} (Phiếu vận hành: {rec.ticket_id.name if rec.ticket_id else 'N/A'})",
                }

                if service_type: # Kiểm tra nếu tìm thấy loại dịch vụ thì bổ sung vào dữ liệu tạo
                    service_vals['service_type_id'] = service_type.id

                service = Service.create(service_vals) # Thực hiện lệnh tạo bản ghi phiếu sửa chữa bên Fleet
                rec.sudo().with_context(skip_sync_fleet=True).write({'service_id': service.id}) # Ghi ID phiếu sửa chữa vừa tạo vào service_id và kẹp cờ skip_sync_fleet
                rec.service_id = service  # Cập nhật trực tiếp vào bộ nhớ RAM để các hàm sau lấy ra dùng ngay mà không cần truy vấn lại DB

    # ---------------------------------------------------------------------
    # HÀM CHO NÚT BẤM LƯU VÀ XỬ LÝ SỰ CỐ
    # ---------------------------------------------------------------------
    def action_create_fleet_service(self):
        """Lưu thay đổi cho sự cố:
        - Nếu cần sửa chữa: tạo phiếu bảo dưỡng / sửa chữa sang Fleet và lưu trạng thái Đang thực hiện ('processing')
        - Nếu không cần sửa chữa: lưu ở trạng thái Hoàn tất ('resolved')
        """
        for rec in self:
            if rec.needs_repair:
                if not rec.vehicle_id:
                    raise UserError(_('Vui lòng chọn xe gặp sự cố trước khi lưu thay đổi.'))
                if not rec.service_id: # Kiểm tra xem sự cố đã có phiếu sửa chữa bên Fleet chưa
                    rec._sync_to_fleet_service() # Gọi hàm đồng bộ sang Fleet
                if rec.status != 'processing': # Kiểm tra và cập nhật trạng thái thành processing
                    rec.write({'status': 'processing'})
            else:
                if rec.status != 'resolved':
                    rec.write({'status': 'resolved'})
        return True

    # ---------------------------------------------------------------------
    # HÀM MỞ HỒ SƠ BẢO DƯỠNG & SỬA CHỮA BÊN FLEET
    # ---------------------------------------------------------------------
    def action_open_fleet_service(self):
        """Mở hồ sơ bảo dưỡng & sửa chữa bên Fleet"""
        self.ensure_one()
        if not self.service_id:
            raise UserError('Sự cố này chưa được liên kết với hồ sơ bảo dưỡng & sửa chữa nào.')
        return {
            'name': 'Hồ sơ bảo dưỡng & sửa chữa',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.log.services',
            'res_id': self.service_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ---------------------------------------------------------------------
    # HÀM MIGRATION NÂNG CẤP DỮ LIỆU CŨ KHI CÀI ĐẶT / UPGRADE MODULE
    # Tự động chạy SQL thuần quét sạch database để chuyển các bản ghi cũ
    # có trạng thái 'new' hoặc NULL sang 'processing', tránh lỗi hiển thị trên giao diện.
    # ---------------------------------------------------------------------
    def init(self):
        super().init()
        self.env.cr.execute("""
            UPDATE rental_operation_incident_log
            SET status = 'processing'
            WHERE status = 'new' OR status IS NULL
        """)

    # ---------------------------------------------------------------------
    # HÀM LẤY NHÃN ĐỊNH DANH SỰ CỐ KÈM XE
    # ---------------------------------------------------------------------
    def _get_incident_label(self):
        self.ensure_one()
        veh_name = self.vehicle_id.display_name or self.vehicle_id.name or 'Xe'
        return f"{self.name} (Xe {veh_name})"

    # ---------------------------------------------------------------------
    # HÀM KÍCH HOẠT 'BẮT ĐẦU XỬ LÝ SỰ CỐ'
    # ---------------------------------------------------------------------
    def action_start_processing(self):
        """Xác nhận bắt đầu xử lý sự cố"""
        for rec in self:
            label = rec._get_incident_label()
            if rec.status == 'resolved':
                raise UserError(f'Sự cố {label} đã được giải quyết hoàn tất!')
            if rec.status == 'processing':
                raise UserError(f'Sự cố {label} đang trong quá trình xử lý!')
            rec.write({
                'status': 'processing',
                'is_selected': False,
            })

    # ---------------------------------------------------------------------
    # HÀM KÍCH HOẠT 'HOÀN TẤT XỬ LÝ SỰ CỐ'
    # ---------------------------------------------------------------------
    def action_resolve(self):
        """Xác nhận sự cố đã được xử lý / khắc phục hoàn tất"""
        for rec in self:
            label = rec._get_incident_label()
            if rec.status == 'resolved':
                raise UserError(f'Sự cố {label} đã hoàn tất trước đó!')
            rec.write({
                'status': 'resolved',
                'is_selected': False,
            })

    # ---------------------------------------------------------------------
    # HÀM KIỂM SOÁT XÓA BẢN GHI
    # ---------------------------------------------------------------------
    def unlink(self):
        """Không cho phép xóa sự cố khi phiếu đã khóa hoặc đã được đồng bộ sang Fleet"""
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không thể xóa sự cố!'))
        records_to_unlink = self.filtered(lambda r: not r.service_id) # Chỉ cho phép xóa những sự cố chưa được đồng bộ sang Fleet (service_id rỗng)
        return super(RentalIncidentLog, records_to_unlink).unlink()
# -*- coding: utf-8 -*-
"""Model Biên lai Giao xe & Trang thiết bị (Delivery Receipt).

- Trạng thái (tự động tính qua _compute_state dựa theo các xe bên trong):
  + Chưa thực hiện (pending): Các xe thuộc biên lai vẫn ở trạng thái Chưa giao.
  + Đang giao xe (delivering): Có ít nhất 1 xe đang đi giao.
  + Đã giao thành công (delivered): Toàn bộ xe trong biên lai đã bàn giao cho khách (renting/returned).
- Hỗ trợ gom nhiều xe cùng địa điểm/thời gian giao thành 1 biên lai in PDF ký nhận.
- Khi bấm Bắt đầu giao / Xác nhận giao trên biên lai sẽ đồng bộ trạng thái cho toàn bộ xe bên trong.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RentalDeliveryReceipt(models.Model):
    _name = 'rental.delivery.receipt'
    _description = 'Biên Lai Giao Xe & Trang Thiết Bị'
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Mã Biên Lai', required=True, copy=False, readonly=True, default='Mới')
    
    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', required=True, ondelete='cascade')
    contract_id = fields.Many2one('rental.contract', string='Hợp đồng thuê', related='ticket_id.contract_id', store=True, readonly=True)
    customer_id = fields.Many2one('res.partner', string='Khách hàng', required=True)
    customer_phone = fields.Char(string='Số điện thoại')

    @api.onchange('customer_id') # Nếu thay đổi khách hàng thì cập nhật số điện thoại
    def _onchange_customer_id(self):
        if self.customer_id:
            self.customer_phone = self.customer_id.phone or self.customer_id.mobile or ''
    
    delivery_date = fields.Date(string='Ngày giao xe')
    delivery_time = fields.Char(string='Giờ giao xe', help='Thời gian giao xe (VD: 08:30)')
    delivery_location = fields.Char(string='Địa điểm giao xe', default='Tại cửa hàng')

    vehicle_ids = fields.Many2many(
        'rental.operation.ticket.vehicle',
        'rental_delivery_receipt_vehicle_rel',
        'receipt_id',
        'vehicle_detail_id',
        string='Danh sách xe bàn giao',
        required=True
    )

    # 4 món phụ kiện đi kèm cố định (tính theo số xe trong biên lai)
    qty_helmet = fields.Integer(string='Mũ bảo hiểm', default=2, required=True)
    qty_raincoat = fields.Integer(string='Áo mưa', default=2, required=True)
    qty_phone_holder = fields.Integer(string='Giá đỡ điện thoại', default=1, required=True)
    qty_charger = fields.Integer(string='Bộ sạc xe', default=1, required=True)

    user_id = fields.Many2one(
        'res.users', 
        string='Nhân viên giao xe', 
        default=lambda self: self.env.user if self.env.user.name not in ('Administrator', 'admin', 'Admin') else False
    )
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)

    is_selected = fields.Boolean(string='Chọn', default=False)
    vehicle_count = fields.Integer(string='Số lượng xe', compute='_compute_vehicle_count')

    # Tính số lượng xe nếu cột danh sách xe thay đổi
    @api.depends('vehicle_ids') 
    def _compute_vehicle_count(self):
        for rec in self:
            rec.vehicle_count = len(rec.vehicle_ids)

    state = fields.Selection([
        ('pending', 'Chưa thực hiện'),
        ('delivering', 'Đang giao xe'),
        ('delivered', 'Đã giao thành công'),
        # Tương thích dữ liệu cũ nếu có
        ('draft', 'Chưa thực hiện'),
        ('confirmed', 'Đã giao thành công'),
    ], string='Trạng thái', default='pending', compute='_compute_state', store=True, readonly=False)

    # Tính số biên lai theo từng trạng thái
    @api.depends('vehicle_ids.status')
    def _compute_state(self):
        for rec in self:
            if not rec.vehicle_ids:
                rec.state = 'pending'
                continue
            statuses = rec.vehicle_ids.mapped('status')
            if all(s in ('renting', 'returned') for s in statuses):
                rec.state = 'delivered'
            elif any(s in ('delivering', 'renting', 'returned') for s in statuses):
                rec.state = 'delivering'
            else:
                rec.state = 'pending'


    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # HÀM CHUYỂN BIÊN LAI THÀNH BẮT ĐẦU GIAO XE
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<    
    def action_start_delivery(self):
        """Bắt đầu giao xe cho biên lai: chuyển biên lai và các xe bên trong sang Đang giao xe"""
        for rec in self:
            # <<<< Kiểm tra bản ghi biên lai có đạt yêu cầu chưa
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa!'))
            if rec.state != 'pending':
                if len(self) == 1:
                    raise UserError(_('Biên lai "%s" không ở trạng thái Chưa thực hiện!') % (rec.name or ''))
                continue
            if not rec.vehicle_ids:
                raise UserError(_('Biên lai "%s" chưa có danh sách xe bàn giao!') % (rec.name or ''))
            # >>>>>>>>>>>>>>

            # 1. Kiểm tra điều kiện Fleet cho tất cả xe trong biên lai
            rec.vehicle_ids._check_fleet_delivery_eligibility()

            # 2. Cập nhật các xe con trong biên lai
            rec.vehicle_ids.write({
                'status': 'delivering',
                'is_selected': False,
            })

            # Cập nhật trạng thái bản ghi trong quản lý xe
            for v in rec.vehicle_ids:
                if v.vehicle_id and not v.subfleet:
                    v.vehicle_id.sudo().write({'operational_status': 'renting'})

            # 3. Cập nhật biên lai
            rec.write({
                'state': 'delivering',
                'is_selected': False,
            })
        return True
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # HÀM CHUYỂN BIÊN LAI THÀNH ĐÃ GIAO XE THÀNH CÔNG
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<    
    def action_confirm_delivery(self):
        """Xác nhận đã giao xe cho biên lai: chuyển biên lai sang Đã giao và các xe sang Đang thuê.
        Không bắt buộc phải ở trạng thái Đang giao xe, có thể chuyển trực tiếp từ Chưa thực hiện sang Đã giao xe.
        """
        now = fields.Datetime.now()

        
        for rec in self:
            # <<<<<<<<<< KIỂM TRA ĐIỀU KIỆN HỢP ĐỒNG VÀ BIÊN LAI
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled':
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa!'))
            if rec.state == 'delivered':
                if len(self) == 1:
                    raise UserError(_('Biên lai "%s" đã ở trạng thái Đã giao thành công!') % (rec.name or ''))
                continue
            if not rec.vehicle_ids:
                raise UserError(_('Biên lai "%s" chưa có danh sách xe bàn giao!') % (rec.name or ''))
            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.

            # 1. Kiểm tra điều kiện Fleet
            rec.vehicle_ids._require_a_returned_before_b_delivery() # Kiểm tra có phải là xe B không, nếu phải thì cần yêu cầu xe A
            rec.vehicle_ids._check_fleet_delivery_eligibility() # Kiểm tra xe có sẵn sàng không

            # 2. Cập nhật các xe con trong biên lai
            for vline in rec.vehicle_ids: # Từng xe con trong biên lai (vehicle_ids này lấy từ bảng chi tiết phiếu VH)
                if vline.status == 'returned':
                    continue

                v_vals = {
                    'status': 'renting',
                    'is_selected': False,
                }
                if not vline.actual_delivery_date: # Nếu không có ngày giao thì lấy now()
                    v_vals['actual_delivery_date'] = now

                vline.write(v_vals) # Ghi dữ liệu vào các xe trong bảng biên lai

                if vline.vehicle_id: # Nếu xe có trong Fleet thì cập nhật sang đang thuê
                    vline.vehicle_id.sudo().write({'operational_status': 'renting'})

                vline._sync_contract_in_progress() # Đưa hợp đồng sang trạng thái Đang thực hiện

            # 3. Trigger cập nhật hợp đồng sang Đang thuê ('in_progress')
            if rec.ticket_id: # Nếu có phiếu vận hành
                if not rec.ticket_id.actual_delivery_date:
                    rec.ticket_id.actual_delivery_date = now
                contract = rec.ticket_id.contract_id
                if contract and contract.state == 'confirmed':
                    contract.sudo().write({'state': 'in_progress'})
                rec.ticket_id._sync_contract_in_progress()

            # 4. Cập nhật biên lai
            rec.write({
                'state': 'delivered',
                'is_selected': False,
            })
            
            # Kiểm tra xem việc giao xe này có liên quan đến case đổi xe nào không, nếu có thì cập nhật phiếu
            rec.vehicle_ids._check_and_sync_vehicle_exchanges()
        return True
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # CREATE MULTI
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới': # Tạo mã tự động
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.delivery.receipt') or 'BLGX'

            if vals.get('ticket_id'): # Kiểm tra xem phiếu có thuộc phiếu VH nào không
                ticket = self.env['rental.operation.ticket'].browse(vals['ticket_id'])

                if ticket.state == 'contract_cancelled': # Kiểm tra điều kiện phiếu vận hành
                    raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không thể tạo biên lai giao xe!'))

                if not vals.get('customer_id') and ticket.customer_id: # Nếu phiếu giao xe chưa có người dùng thì lấy ID từ phiếu VH
                    vals['customer_id'] = ticket.customer_id.id
                    
            if not vals.get('customer_phone') and vals.get('customer_id'): # Nếu chưa có SĐT thì lấy từ bảng Partner (bảng đối tác/khách hàng) theo customer_id
                partner = self.env['res.partner'].browse(vals['customer_id'])
                vals['customer_phone'] = partner.phone or partner.mobile or ''

        receipts = super(RentalDeliveryReceipt, self).create(vals_list) # Tạo bản ghi mới vào phiếu
        return receipts
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # HÀM WRITE
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<    
    def write(self, vals):
        for rec in self:
            if rec.ticket_id and rec.ticket_id.state == 'contract_cancelled': # Kiểm tra hợp đồng
                raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa, không thể chỉnh sửa biên lai!'))

        # Nếu có cập nhật các trường thông tin biên lai (ngoài is_selected và state)
        if any(k not in ('is_selected', 'state') for k in vals.keys()):
            delivered_recs = self.filtered(lambda r: r.state == 'delivered') # Lấy những biên lai ở trạng thái đã được giao thành công
            if delivered_recs: # Xác định có biên lai đã giao xe
                # Nếu chỉ có duy nhất biên lai đã giao thành công được sửa
                if len(self) == 1: # Nếu có 1 cái tức: 1 cái này chính là cái đã giao, không được sửa nữa
                    raise UserError(_('Biên lai "%s" đã giao thành công, không được phép chỉnh sửa!') % (delivered_recs[0].name or ''))
                # Nếu sửa nhiều biên lai cùng lúc, chỉ cập nhật cho các biên lai chưa giao thành công
                updatable_recs = self - delivered_recs # Loại bỏ các biên lai đã hoàn thành
                if updatable_recs: # Chỉ cập nhật các biên lai chưa hoàn thành
                    return super(RentalDeliveryReceipt, updatable_recs).write(vals)
                return True

        return super(RentalDeliveryReceipt, self).write(vals)
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # Mở chi tiết các xe trong biên lai giao xe dạng modal popup (chỉ xem) khi ở trang danh sách các biên lai
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<    
    def action_open_receipt_detail(self):
        """Mở chi tiết biên lai giao xe dạng modal popup (chỉ xem)"""
        self.ensure_one()

        # Lấy ID của View Form giao xe đang hiển thị trên giao diện
        view_id = self.env.ref('motorbike_rental_operation.view_rental_delivery_receipt_form', raise_if_not_found=False)
        return {
            'name': _('Chi Tiết Biên Lai: %s') % (self.name or ''),
            'type': 'ir.actions.act_window',
            'res_model': 'rental.delivery.receipt',
            'res_id': self.id,
            'views': [(view_id.id, 'form')] if view_id else [(False, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'flags': {'mode': 'readonly'},
            'context': {
                'default_ticket_id': self.ticket_id.id,
                'create': False,
                'edit': False,
                'delete': False,
            },
        }
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # LƯU THAY ĐỔI TRÊN BIÊN LAI GIAO XE, KHI CẬP NHẬT BIÊN LAI GIAO XE
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<    
    def action_save_changes(self):
        """Lưu thay đổi trên biên lai giao xe và đồng bộ thông tin nếu có"""
        self.ensure_one()

        if self.ticket_id and self.ticket_id.state == 'contract_cancelled':
            raise UserError(_('Phiếu vận hành đã ở trạng thái "Hợp đồng bị hủy" và đã bị khóa!'))
        if self.state == 'delivered':
            raise UserError(_('Biên lai đã giao thành công, không thể chỉnh sửa!'))

        for veh in self.vehicle_ids:
            if veh.status in ('waiting', 'delivering'): # Nếu chờ giao hoặc đang giao mới cho sửa
                v_vals = {}
                # <<<< Cập nhật thông tin giao xe (Có đặt cờ để không bị ghi đè khi chỉnh sửa chung)
                if self.delivery_date and veh.delivery_date != self.delivery_date:
                    v_vals['delivery_date'] = self.delivery_date
                    v_vals['is_custom_delivery_date'] = True
                if self.delivery_time and veh.delivery_time != self.delivery_time:
                    v_vals['delivery_time'] = self.delivery_time
                    v_vals['is_custom_delivery_time'] = True
                if self.delivery_location and veh.delivery_location != self.delivery_location:
                    v_vals['delivery_location'] = self.delivery_location
                    v_vals['is_custom_delivery_location'] = True
                if v_vals:
                    veh.write(v_vals)

        return {'type': 'ir.actions.act_window_close'}
    
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # HÀM KIỂM TRA VIỆC XÓA
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<    
    def unlink(self):
        if not self.env.context.get('allow_wizard_cleanup'): # 'allow_wizard_cleanup' được cấp khi wizard dọn dẹp
            raise UserError(_('Biên lai chỉ được phép xem, không được phép xóa!'))
        return super(RentalDeliveryReceipt, self).unlink()


    def action_print_receipt(self):
        """In lại biên lai giao xe dạng PDF"""
        self.ensure_one()
        for veh in self.vehicle_ids:
            if not veh.delivery_visual_note or veh.delivery_visual_note in (  # Kiểm tra xem có ghi chú không
                'Ngoại quan của xe không có vấn đề',
                'Xe vận hành tốt, ngoại quan bình thường, không trầy xước phát sinh.'
            ):
                veh_condition = veh._get_vehicle_exterior_condition(veh.vehicle_id) if veh.vehicle_id else False
                if veh_condition and veh_condition != 'Ngoại quan của xe không có vấn đề':
                    veh.sudo().write({'delivery_visual_note': veh_condition})

        return self.env.ref('motorbike_rental_operation.action_report_delivery_receipt').report_action(self) 
        # report_action phương thức sẵn có trong Odoo để in báo cáo
        # 'action_report_delivery_receipt' id của đối tượng được định nghĩa trong file XML => report/delivery_receipt_report.xml

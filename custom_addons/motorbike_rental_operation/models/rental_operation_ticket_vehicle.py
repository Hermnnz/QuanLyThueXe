# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class RentalOperationTicketVehicle(models.Model):
    _name = 'rental.operation.ticket.vehicle'
    _description = 'Chi tiết Xe Vận Hành'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', ondelete='cascade')
    rental_order_ref = fields.Char(string='Thuộc Đơn thuê', related='ticket_id.rental_order_ref', readonly=True)

    # Ô tick chọn phục vụ thao tác hàng loạt
    is_selected = fields.Boolean(string='Chọn', default=False)

    @api.onchange('is_selected')
    def _onchange_is_selected(self):
        if self.ticket_id:
            if self.ticket_id.state == 'done' or (self.ticket_id.contract_id and self.ticket_id.contract_id.state == 'done'):
                self.is_selected = False
                self.ticket_id.has_selected_vehicles = False
                return
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
    vehicle_price = fields.Monetary(string='Giá tiền xe', default=0.0, currency_field='currency_id')

    # Thông tin vận chuyển - Mặc định lấy từ địa điểm chung của hợp đồng/phiếu
    delivery_location = fields.Char(string='Vị trí giao', default='Tại cửa hàng')
    return_location = fields.Char(string='Vị trí thu hồi', default='Tại cửa hàng')
    delivery_time = fields.Char(string='Giờ giao xe', default=False, help='Thời gian dự kiến giao xe (VD: 08:30)')

    # Đánh dấu người dùng đã chỉnh riêng địa điểm / thời gian (không bị ghi đè khi đổi giá trị chung)
    is_custom_delivery_location = fields.Boolean(string='Chỉnh địa điểm giao riêng', default=False)
    is_custom_return_location = fields.Boolean(string='Chỉnh địa điểm thu hồi riêng', default=False)
    is_custom_delivery_time = fields.Boolean(string='Chỉnh giờ giao riêng', default=False)

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
        if self.ticket_id and self.return_location != self.ticket_id.quick_return_location:
            self.is_custom_return_location = True

    @api.onchange('delivery_time')
    def _onchange_delivery_time(self):
        if self.status in ('renting', 'returned'):
            name = self._get_vehicle_label()
            raise UserError(f'Xe {name} đã được bàn giao (hoặc đã thu hồi), không được phép chỉnh sửa Giờ giao xe!')
        if self.ticket_id and hasattr(self.ticket_id, 'quick_delivery_time') and self.delivery_time != self.ticket_id.quick_delivery_time:
            self.is_custom_delivery_time = True

    # Thông tin Biên lai bàn giao xe & Phụ kiện đi kèm (lưu vết phục vụ khi Thu hồi xe)
    delivery_receipt_id = fields.Many2one('rental.delivery.receipt', string='Biên lai giao xe', readonly=True)
    delivery_receipt_issued = fields.Boolean(string='Đã xuất biên lai', default=False, readonly=True)
    receipt_printed_at = fields.Datetime(string='Thời điểm xuất biên lai', readonly=True)

    # 4 món phụ kiện đi kèm cố định (mặc định 2 mũ, 2 áo mưa, 1 giá đt, 1 sạc/xe)
    qty_helmet = fields.Integer(string='Mũ bảo hiểm', default=2)
    qty_raincoat = fields.Integer(string='Áo mưa', default=2)
    qty_phone_holder = fields.Integer(string='Giá đỡ điện thoại', default=1)
    qty_charger = fields.Integer(string='Bộ sạc xe', default=1)

    # Tình trạng ngoại quan lúc giao xe
    delivery_visual_note = fields.Text(
        string='Ngoại quan khi giao',
        default='Ngoại quan của xe không có vấn đề'
    )

    @api.model
    def _get_vehicle_exterior_condition(self, vehicle):
        """
        Lấy thông tin ngoại quan xe từ trường description trên fleet.vehicle (tab 'Mô tả tình trạng').
        Nếu không có giá trị gì, mặc định là: 'Ngoại quan của xe không có vấn đề'
        """
        default_val = 'Ngoại quan của xe không có vấn đề'
        if not vehicle:
            return default_val

        if isinstance(vehicle, int):
            vehicle = self.env['fleet.vehicle'].browse(vehicle)
        if not vehicle.exists():
            return default_val

        v_sudo = vehicle.sudo()
        note = False
        for field_name in ('description', 'exterior_condition', 'visual_notes'):
            if hasattr(v_sudo, field_name):
                raw_val = getattr(v_sudo, field_name)
                if raw_val:
                    if isinstance(raw_val, str) and ('<' in raw_val and '>' in raw_val):
                        from odoo.tools import html2plaintext
                        cleaned = html2plaintext(raw_val).strip()
                    else:
                        cleaned = str(raw_val).strip()
                    if cleaned:
                        note = cleaned
                        break
        return note or default_val

    def _get_display_visual_note(self):
        """Lấy tình trạng ngoại quan chuẩn xác nhất để hiển thị và xuất báo cáo PDF"""
        self.ensure_one()
        note = (self.delivery_visual_note or '').strip()
        # Nếu đã có ghi chú cụ thể khác các câu mặc định
        if note and note not in (
            'Ngoại quan của xe không có vấn đề',
            'Xe vận hành tốt, ngoại quan bình thường, không trầy xước phát sinh.'
        ):
            return note

        # Nếu chưa có hoặc chỉ là câu mặc định, ưu tiên lấy từ 'Mô tả tình trạng' của fleet.vehicle
        if self.vehicle_id:
            veh_cond = self._get_vehicle_exterior_condition(self.vehicle_id)
            if veh_cond and veh_cond != 'Ngoại quan của xe không có vấn đề':
                return veh_cond

        return note or 'Ngoại quan của xe không có vấn đề'

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id_exterior(self):
        if self.vehicle_id:
            veh_note = self._get_vehicle_exterior_condition(self.vehicle_id)
            if not self.delivery_visual_note or self.delivery_visual_note in (
                'Xe vận hành tốt, ngoại quan bình thường, không trầy xước phát sinh.',
                'Ngoại quan của xe không có vấn đề'
            ) or (veh_note and veh_note != 'Ngoại quan của xe không có vấn đề'):
                self.delivery_visual_note = veh_note

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('vehicle_id'):
                vehicle = self.env['fleet.vehicle'].browse(vals['vehicle_id'])
                veh_condition = self._get_vehicle_exterior_condition(vehicle)
                note_in_vals = (vals.get('delivery_visual_note') or '').strip()
                if not note_in_vals or note_in_vals in (
                    'Ngoại quan của xe không có vấn đề',
                    'Xe vận hành tốt, ngoại quan bình thường, không trầy xước phát sinh.'
                ):
                    vals['delivery_visual_note'] = veh_condition
                elif veh_condition and veh_condition != 'Ngoại quan của xe không có vấn đề' and note_in_vals == 'Ngoại quan của xe không có vấn đề':
                    vals['delivery_visual_note'] = veh_condition
        return super(RentalOperationTicketVehicle, self).create(vals_list)

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

    def _get_vehicle_label(self):
        self.ensure_one()
        if self.vehicle_id:
            return self.vehicle_id.display_name or self.vehicle_id.name or 'N/A'
        return 'không xác định'

    def action_start_delivery(self):
        """Bắt đầu giao xe cho từng chiếc - Cập nhật xe bên Bắc sang Đang cho thuê (renting)"""
        for rec in self:
            name = rec._get_vehicle_label()
            if rec.status == 'returned':
                raise UserError(f'Xe {name} đã được thu hồi!')
            if rec.status == 'renting':
                raise UserError(f'Xe {name} đã được giao!')
            rec.write({
                'status': 'delivering',
                'is_selected': False,
            })
            if rec.vehicle_id:
                rec.vehicle_id.write({'operational_status': 'renting'})

    @api.model_create_multi
    def create(self, vals_list):
        records = super(RentalOperationTicketVehicle, self).create(vals_list)
        for rec in records:
            if rec.status == 'renting':
                rec._sync_contract_in_progress()
                if rec.vehicle_id:
                    rec.vehicle_id.write({'operational_status': 'renting'})
        return records

    def _sync_contract_in_progress(self):
        """Khi có xe trong bản ghi giao xe được giao ('renting'), chuyển hợp đồng sang Đang thuê ('in_progress')"""
        for rec in self:
            contract = rec.ticket_id.contract_id if rec.ticket_id else False
            if contract and contract.state not in ('in_progress', 'done', 'cancelled'):
                if contract.state == 'draft':
                    contract.action_confirm()
                if contract.state == 'confirmed':
                    contract.write({'state': 'in_progress'})

    def action_confirm_delivery(self):
        """Xác nhận đã bàn giao xe thành công cho khách - Xe bên Bắc ở trạng thái Đang cho thuê (renting)"""
        for rec in self:
            name = rec._get_vehicle_label()
            if rec.status == 'returned':
                raise UserError(f'Xe {name} đã được thu hồi!')
            if rec.status == 'renting':
                raise UserError(f'Xe {name} đã được giao!')
            vals = {
                'status': 'renting',
                'is_selected': False,
            }
            if not rec.actual_delivery_date:
                vals['actual_delivery_date'] = fields.Datetime.now()
            rec.write(vals)
            if rec.ticket_id and not rec.ticket_id.actual_delivery_date:
                rec.ticket_id.actual_delivery_date = fields.Datetime.now()
            rec._sync_contract_in_progress()
            if rec.vehicle_id:
                rec.vehicle_id.write({'operational_status': 'renting'})

    def action_confirm_return(self):
        """Xác nhận thu hồi xe từ khách - Mặc định xe bên Bắc chuyển sang Chờ kiểm tra (pending_inspection)"""
        for rec in self:
            name = rec._get_vehicle_label()
            if rec.status in ('waiting', 'delivering'):
                raise UserError(f'Xe {name} chưa được bàn giao!')
            if rec.status == 'returned':
                raise UserError(f'Xe {name} đã được thu hồi!')
            vals = {
                'status': 'returned',
                'is_selected': False,
            }
            if not rec.actual_return_date:
                vals['actual_return_date'] = fields.Datetime.now()
            rec.write(vals)
            if rec.ticket_id:
                all_returned = all(v.status == 'returned' for v in rec.ticket_id.vehicle_detail_ids)
                if all_returned:
                    if not rec.ticket_id.actual_return_date:
                        rec.ticket_id.actual_return_date = fields.Datetime.now()
            if rec.vehicle_id:
                rec.vehicle_id.write({
                    'operational_status': 'pending_inspection',
                    'technical_ready': False,
                })

    def write(self, vals):
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

        res = super(RentalOperationTicketVehicle, self).write(vals)
        if 'status' in vals:
            for rec in self:
                if rec.vehicle_id:
                    if vals['status'] in ('delivering', 'renting'):
                        rec.vehicle_id.write({'operational_status': 'renting'})
                    elif vals['status'] == 'returned':
                        rec.vehicle_id.write({
                            'operational_status': 'pending_inspection',
                            'technical_ready': False,
                        })
                # Khi xe ở trạng thái đã giao xe ('renting'), hợp đồng chuyển sang trạng thái Đang thuê ('in_progress')
                if vals['status'] == 'renting':
                    rec._sync_contract_in_progress()
        return res

    def action_reset_waiting(self):
        """Khôi phục về trạng thái chưa giao"""
        for rec in self:
            rec.write({
                'status': 'waiting',
                'is_selected': False,
            })

    def unlink(self):
        for rec in self:
            if rec.ticket_id and not self.env.context.get('delete_ticket'):
                raise UserError('Không được phép xóa xe khỏi phiếu bàn giao! Danh sách xe được lấy theo hợp đồng thuê.')
        return super(RentalOperationTicketVehicle, self).unlink()

# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RentalOperationTicket(models.Model):
    _name = 'rental.operation.ticket'
    _description = 'Phiếu Vận Hành Tổng (Giao Nhận)'

    name = fields.Char(string='Mã Vận Hành (Mã OP)', required=True, copy=False, readonly=True, default='Mới')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.operation.ticket')
        return super(RentalOperationTicket, self).create(vals_list)

    rental_order_ref = fields.Char(string='Mã Đơn thuê')
    expected_checkout = fields.Datetime(string='Ngày Giao Xe')
    rental_duration_days = fields.Integer(string='Thời gian thuê (Ngày)', default=1)
    expected_checkin = fields.Datetime(string='Ngày Trả Xe', compute='_compute_expected_checkin', store=True, readonly=False)
    
    @api.depends('expected_checkout', 'rental_duration_days')
    def _compute_expected_checkin(self):
        for rec in self:
            if rec.expected_checkout and rec.rental_duration_days:
                # Cần import timedelta từ datetime ở đầu file
                from datetime import timedelta
                rec.expected_checkin = rec.expected_checkout + timedelta(days=rec.rental_duration_days)
            elif not rec.expected_checkin:
                rec.expected_checkin = rec.expected_checkout

    @api.onchange('expected_checkout', 'expected_checkin')
    def _onchange_expected_dates(self):
        # Tự động cập nhật ngày giao/nhận cho các xe bên dưới khi đổi ngày ở phiếu tổng
        for line in self.vehicle_detail_ids:
            if self.expected_checkout:
                line.date_checkout = self.expected_checkout
            if self.expected_checkin:
                line.date_checkin = self.expected_checkin
                
    # Trường ảo (Không lưu DB) dùng để điền nhanh thông tin giao/nhận cho tất cả các xe
    quick_delivery_location = fields.Char(string='Địa điểm Giao', store=False)
    quick_delivery_fee = fields.Float(string='Phí Giao', store=False)
    quick_return_location = fields.Char(string='Địa điểm Nhận', store=False)
    quick_return_fee = fields.Float(string='Phí Nhận', store=False)

    @api.onchange('quick_delivery_location', 'quick_delivery_fee', 'quick_return_location', 'quick_return_fee')
    def _onchange_quick_delivery_info(self):
        for line in self.vehicle_detail_ids:
            if self.quick_delivery_location:
                line.delivery_location = self.quick_delivery_location
            # Always update fee if it is entered, even if it's 0 (maybe user wants to zero it out)
            if self.quick_delivery_fee is not False:
                line.delivery_fee = self.quick_delivery_fee
            if self.quick_return_location:
                line.return_location = self.quick_return_location
            if self.quick_return_fee is not False:
                line.return_fee = self.quick_return_fee
    
    # Tiền thuê gốc và giấy tờ
    total_rent_amount = fields.Float(string='Tổng tiền', compute='_compute_total_rent', store=True)
    deposit_amount = fields.Float(string='Đã cọc', default=0.0)
    remaining_rent_amount = fields.Float(string='Số tiền còn lại', compute='_compute_remaining_rent', store=True)

    @api.depends('vehicle_detail_ids.vehicle_price', 'rental_duration_days')
    def _compute_total_rent(self):
        for rec in self:
            # Tổng tiền = Tổng giá xe * Số ngày thuê
            base_price = sum(rec.vehicle_detail_ids.mapped('vehicle_price'))
            rec.total_rent_amount = base_price * (rec.rental_duration_days or 1)

    @api.depends('total_rent_amount', 'deposit_amount')
    def _compute_remaining_rent(self):
        for rec in self:
            rec.remaining_rent_amount = rec.total_rent_amount - rec.deposit_amount
    is_rent_paid = fields.Boolean(string='Đã thanh toán tiền thuê')
    is_id_card_kept = fields.Boolean(string='Đã thu CCCD gốc')
    
    # Tài chính phát sinh (Ship + Đền bù)
    total_incurred_cost = fields.Float(string='Tổng chi phí phát sinh', compute='_compute_costs', store=True)
    paid_incurred_cost = fields.Float(string='Chi phí phát sinh đã thanh toán', compute='_compute_costs', store=True)
    remaining_cost = fields.Float(string='Chi phí phát sinh còn lại', compute='_compute_costs', store=True)
    is_incurred_cost_paid = fields.Boolean(string='Đã thanh toán chi phí phát sinh')
    
    # Liên kết bảng con
    vehicle_detail_ids = fields.One2many('rental.operation.ticket.vehicle', 'ticket_id', string='Chi tiết Xe')
    incident_ids = fields.One2many('rental.operation.incident.log', 'ticket_id', string='Sự cố & Hư hỏng')
    
    state = fields.Selection([
        ('waiting', 'Chưa thực hiện'),
        ('renting', 'Thực hiện'),
        ('done', 'Hoàn tất')
    ], string='Trạng thái HĐ', default='waiting')

    @api.depends('incident_ids.cost', 'incident_ids.is_paid', 
                 'vehicle_detail_ids.delivery_fee', 'vehicle_detail_ids.is_delivery_fee_paid',
                 'vehicle_detail_ids.return_fee', 'vehicle_detail_ids.is_return_fee_paid')
    def _compute_costs(self):
        for rec in self:
            # Tính tổng phát sinh
            total_damage = sum(rec.incident_ids.mapped('cost'))
            total_delivery = sum(rec.vehicle_detail_ids.mapped('delivery_fee'))
            total_return = sum(rec.vehicle_detail_ids.mapped('return_fee'))
            total = total_damage + total_delivery + total_return
            
            # Tính tổng đã thanh toán
            paid_damage = sum(incident.cost for incident in rec.incident_ids if incident.is_paid)
            paid_delivery = sum(v.delivery_fee for v in rec.vehicle_detail_ids if v.is_delivery_fee_paid)
            paid_return = sum(v.return_fee for v in rec.vehicle_detail_ids if v.is_return_fee_paid)
            paid = paid_damage + paid_delivery + paid_return
            
            rec.total_incurred_cost = total
            rec.paid_incurred_cost = paid
            rec.remaining_cost = total - paid


class RentalOperationTicketVehicle(models.Model):
    _name = 'rental.operation.ticket.vehicle'
    _description = 'Chi tiết Xe Vận Hành'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', ondelete='cascade')
    rental_order_ref = fields.Char(string='Thuộc Đơn thuê', related='ticket_id.rental_order_ref', readonly=True)
    
    vehicle_id = fields.Many2one('fleet.vehicle', string='Xe', required=True)
    vehicle_price = fields.Float(string='Giá tiền xe', default=0.0)

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            self.vehicle_price = self.vehicle_id.price
        else:
            self.vehicle_price = 0.0

    # Thông tin vận chuyển
    delivery_location = fields.Char(string='Vị trí giao xe')
    delivery_fee = fields.Float(string='Phí giao xe', default=False)
    is_delivery_fee_paid = fields.Boolean(string='Đã thanh toán phí giao')
    
    return_location = fields.Char(string='Vị trí nhận xe')
    return_fee = fields.Float(string='Phí nhận xe', default=False)
    is_return_fee_paid = fields.Boolean(string='Đã thanh toán phí nhận')
    
    # Lịch trình
    date_checkout = fields.Datetime(string='Ngày Giao Xe')
    date_checkin = fields.Datetime(string='Ngày Trả Xe')
    
    status = fields.Selection([
        ('renting', 'Đang cho thuê'),
        ('returned', 'Đã thu hồi')
    ], string='Trạng thái Xe', default='renting')

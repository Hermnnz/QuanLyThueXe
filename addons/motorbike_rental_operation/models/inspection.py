# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RentalOperationTicket(models.Model):
    _name = 'rental.operation.ticket'
    _description = 'Phiếu Vận Hành Tổng (Giao Nhận)'

    name = fields.Char(string='Mã Vận Hành (Mã OP)', required=True, copy=False, readonly=True, default='Mới')
    rental_order_ref = fields.Char(string='Mã Đơn thuê')
    
    # Tiền thuê gốc và giấy tờ
    total_rent_amount = fields.Float(string='Tổng tiền cần thu (Tiền thuê)')
    rent_payment_proof = fields.Binary(string='Ảnh minh chứng CK tiền thuê')
    is_id_card_kept = fields.Boolean(string='Đã thu CCCD gốc')
    scanned_contract = fields.Binary(string='Bản scan hợp đồng giấy')
    
    # Tài chính phát sinh (Ship + Đền bù)
    total_incurred_cost = fields.Float(string='Tổng chi phí phát sinh', compute='_compute_costs', store=True)
    paid_incurred_cost = fields.Float(string='Chi phí phát sinh đã thanh toán', compute='_compute_costs', store=True)
    remaining_cost = fields.Float(string='Chi phí phát sinh còn lại', compute='_compute_costs', store=True)
    transfer_evidence = fields.Binary(string='Ảnh minh chứng CK tiền phát sinh')
    
    # Liên kết bảng con
    vehicle_detail_ids = fields.One2many('rental.operation.ticket.vehicle', 'ticket_id', string='Chi tiết Xe')
    incident_ids = fields.One2many('rental.operation.incident.log', 'ticket_id', string='Sự cố & Hư hỏng')
    
    state = fields.Selection([
        ('waiting', 'Đang chờ giao'),
        ('renting', 'Đang cho thuê'),
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
    
    vehicle_ref = fields.Char(string='Mã Xe', required=True)
    
    # Thông tin vận chuyển
    delivery_location = fields.Char(string='Vị trí giao xe')
    delivery_fee = fields.Float(string='Phí giao xe')
    is_delivery_fee_paid = fields.Boolean(string='Đã thanh toán phí giao')
    
    return_location = fields.Char(string='Vị trí nhận xe')
    return_fee = fields.Float(string='Phí nhận xe')
    is_return_fee_paid = fields.Boolean(string='Đã thanh toán phí nhận')
    
    # Lịch trình
    date_checkout = fields.Datetime(string='Ngày Giao Xe')
    date_checkin = fields.Datetime(string='Ngày Nhận Lại')
    
    status = fields.Selection([
        ('renting', 'Đang cho thuê'),
        ('returned', 'Đã thu hồi')
    ], string='Trạng thái Xe', default='renting')

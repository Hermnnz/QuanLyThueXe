# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RentalOperationTicketVehicle(models.Model):
    _name = 'rental.operation.ticket.vehicle'
    _description = 'Chi tiết Xe Vận Hành'

    ticket_id = fields.Many2one('rental.operation.ticket', string='Phiếu Vận Hành', ondelete='cascade')
    rental_order_ref = fields.Char(string='Thuộc Đơn thuê', related='ticket_id.rental_order_ref', readonly=True)
    
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

    # Thông tin vận chuyển
    delivery_location = fields.Char(string='Vị trí giao xe')
    delivery_fee = fields.Monetary(string='Phí giao xe', default=0.0, currency_field='currency_id')
    is_delivery_fee_paid = fields.Boolean(string='Đã thanh toán phí giao')
    
    return_location = fields.Char(string='Vị trí nhận xe')
    return_fee = fields.Monetary(string='Phí nhận xe', default=0.0, currency_field='currency_id')
    is_return_fee_paid = fields.Boolean(string='Đã thanh toán phí nhận')
    
    # Lịch trình
    date_checkout = fields.Datetime(string='Ngày Giao Xe')
    date_checkin = fields.Datetime(string='Ngày Trả Xe')
    
    status = fields.Selection([
        ('renting', 'Đang cho thuê'),
        ('returned', 'Đã thu hồi')
    ], string='Trạng thái Xe', default='renting')

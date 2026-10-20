# -*- coding: utf-8 -*-
from odoo import models, fields, api
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
    
    delivery_date = fields.Date(string='Ngày giao xe', default=fields.Date.context_today, required=True)
    delivery_time = fields.Char(string='Giờ giao xe', required=True, default='08:00', help='Thời gian giao xe (VD: 08:30)')
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

    user_id = fields.Many2one('res.users', string='Nhân viên giao xe', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Công ty', default=lambda self: self.env.company)

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã bàn giao')
    ], string='Trạng thái', default='confirmed', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.delivery.receipt') or 'BLGX'
            if not vals.get('customer_id') and vals.get('ticket_id'):
                ticket = self.env['rental.operation.ticket'].browse(vals['ticket_id'])
                if ticket.customer_id:
                    vals['customer_id'] = ticket.customer_id.id
            if not vals.get('customer_phone') and vals.get('customer_id'):
                partner = self.env['res.partner'].browse(vals['customer_id'])
                vals['customer_phone'] = partner.phone or partner.mobile or ''
        return super(RentalDeliveryReceipt, self).create(vals_list)

    def action_print_receipt(self):
        """In lại biên lai giao xe dạng PDF"""
        self.ensure_one()
        return self.env.ref('motorbike_rental_operation.action_report_delivery_receipt').report_action(self)

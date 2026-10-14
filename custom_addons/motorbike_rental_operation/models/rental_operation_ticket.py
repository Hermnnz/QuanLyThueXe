# -*- coding: utf-8 -*-
from datetime import timedelta
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

    # Hợp đồng thuê xe liên kết
    contract_id = fields.Many2one('rental.contract', string='Hợp đồng thuê', required=True)
    customer_id = fields.Many2one('res.partner', string='Khách hàng', related='contract_id.customer_id', store=True, readonly=True)

    rental_order_ref = fields.Char(related='contract_id.name', string='Mã hợp đồng', store=True, readonly=True)
    actual_return_date = fields.Datetime(string='Giờ trả thực tế')

    # TỰ ĐỘNG GỌI DỮ LIỆU TỪ HỢP ĐỒNG ĐỂ FILL VÀO PHIẾU BÀN GIAO
    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if not self.contract_id:
            return

        # Tự động đổ danh sách xe từ hợp đồng sang danh sách xe bàn giao
        vehicle_lines = []
        for line in self.contract_id.line_ids:
            if line.vehicle_id:
                vehicle_vals = {
                    'vehicle_id': line.vehicle_id.id,
                    'vehicle_price': line.daily_rate,
                    'date_checkout': self.contract_id.start_date,
                    'date_checkin': self.contract_id.end_date,
                    'status': 'renting',
                }
                vehicle_lines.append((0, 0, vehicle_vals))

        # (5, 0, 0) xóa sạch các dòng cũ nếu đổi hợp đồng, sau đó nạp các dòng xe mới
        self.vehicle_detail_ids = [(5, 0, 0)] + vehicle_lines

    expected_checkout = fields.Datetime(string='Ngày Giao Xe', related='contract_id.start_date', store=True, readonly=True)
    rental_duration_days = fields.Integer(string='Thời gian thuê (Ngày)', related='contract_id.rental_days', store=True, readonly=True)
    expected_checkin = fields.Datetime(string='Ngày Trả Xe', related='contract_id.end_date', store=True, readonly=True)

    # Tiền tệ
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        related='contract_id.currency_id',
        store=True,
        readonly=True,
    )
    deposit_amount = fields.Monetary(string='Đã cọc', related='contract_id.deposit_amount', store=True, readonly=True, currency_field='currency_id')

    # Trường ảo (Không lưu DB) dùng để điền nhanh thông tin giao/nhận cho tất cả các xe
    quick_delivery_location = fields.Char(string='Địa điểm Giao', store=False)
    quick_delivery_fee = fields.Monetary(string='Phí Giao', store=False, currency_field='currency_id')
    quick_return_location = fields.Char(string='Địa điểm Nhận', store=False)
    quick_return_fee = fields.Monetary(string='Phí Nhận', store=False, currency_field='currency_id')

    @api.onchange('quick_delivery_location', 'quick_delivery_fee', 'quick_return_location', 'quick_return_fee')
    def _onchange_quick_delivery_info(self):
        for line in self.vehicle_detail_ids:
            if self.quick_delivery_location:
                line.delivery_location = self.quick_delivery_location
            if self.quick_delivery_fee is not False:
                line.delivery_fee = self.quick_delivery_fee
            if self.quick_return_location:
                line.return_location = self.quick_return_location
            if self.quick_return_fee is not False:
                line.return_fee = self.quick_return_fee
    
    # Tiền thuê gốc và giấy tờ
    total_rent_amount = fields.Monetary(string='Tổng tiền', compute='_compute_total_rent', store=True, currency_field='currency_id')
    deposit_amount = fields.Monetary(string='Đã cọc', default=0.0, currency_field='currency_id')
    remaining_rent_amount = fields.Monetary(string='Số tiền còn lại', compute='_compute_remaining_rent', store=True, currency_field='currency_id')

    @api.depends('vehicle_detail_ids.vehicle_price', 'vehicle_detail_ids.delivery_fee', 'rental_duration_days')
    def _compute_total_rent(self):
        for rec in self:
            base_price = sum(rec.vehicle_detail_ids.mapped('vehicle_price'))
            total_delivery_fee = sum(rec.vehicle_detail_ids.mapped('delivery_fee'))
            rec.total_rent_amount = base_price * (rec.rental_duration_days or 1) + total_delivery_fee

    @api.depends('total_rent_amount', 'deposit_amount')
    def _compute_remaining_rent(self):
        for rec in self:
            rec.remaining_rent_amount = rec.total_rent_amount - rec.deposit_amount

    def action_confirm_delivery(self):
        for rec in self:
            rec.state = 'renting'
            rec.vehicle_detail_ids.write({'status': 'renting'})

    def action_confirm_return(self):
        for rec in self:
            rec.state = 'done'
            rec.actual_return_date = fields.Datetime.now()
            rec.vehicle_detail_ids.write({'status': 'returned'})

    def action_reset_waiting(self):
        for rec in self:
            rec.state = 'waiting'

    # Tài chính phát sinh (Ship + Đền bù)
    total_incurred_cost = fields.Monetary(string='Tổng chi phí phát sinh', compute='_compute_costs', store=True, currency_field='currency_id')
    paid_incurred_cost = fields.Monetary(string='Chi phí phát sinh đã thanh toán', compute='_compute_costs', store=True, currency_field='currency_id')
    remaining_cost = fields.Monetary(string='Chi phí phát sinh còn lại', compute='_compute_costs', store=True, currency_field='currency_id')
    is_incurred_cost_paid = fields.Boolean(string='Đã thanh toán chi phí phát sinh')
    
    # Liên kết bảng con
    vehicle_detail_ids = fields.One2many('rental.operation.ticket.vehicle', 'ticket_id', string='Chi tiết Xe')
    incident_ids = fields.One2many('rental.operation.incident.log', 'ticket_id', string='Sự cố & Hư hỏng')
    
    state = fields.Selection([
        ('waiting', 'Chưa thực hiện'),
        ('renting', 'Đang cho thuê'),
        ('done', 'Hoàn tất')
    ], string='Trạng thái HĐ', default='waiting')

    @api.depends('incident_ids.cost', 'incident_ids.is_paid', 
                 'vehicle_detail_ids.delivery_fee', 'vehicle_detail_ids.is_delivery_fee_paid',
                 'vehicle_detail_ids.return_fee', 'vehicle_detail_ids.is_return_fee_paid')
    def _compute_costs(self):
        for rec in self:
            total_damage = sum(rec.incident_ids.mapped('cost'))
            total_delivery = sum(rec.vehicle_detail_ids.mapped('delivery_fee'))
            total_return = sum(rec.vehicle_detail_ids.mapped('return_fee'))
            total = total_damage + total_delivery + total_return
            
            paid_damage = sum(incident.cost for incident in rec.incident_ids if incident.is_paid)
            paid_delivery = sum(v.delivery_fee for v in rec.vehicle_detail_ids if v.is_delivery_fee_paid)
            paid_return = sum(v.return_fee for v in rec.vehicle_detail_ids if v.is_return_fee_paid)
            paid = paid_damage + paid_delivery + paid_return
            
            rec.total_incurred_cost = total
            rec.paid_incurred_cost = paid
            rec.remaining_cost = total - paid

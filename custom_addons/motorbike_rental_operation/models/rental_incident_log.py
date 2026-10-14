# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RentalIncidentLog(models.Model):
    _name = 'rental.operation.incident.log'
    _description = 'Nhật ký Sự cố & Hư hỏng'

    name = fields.Char(string='Mã Ghi nhận (Mã INC)', required=True, copy=False, readonly=True, default='Mới')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.operation.incident.log')
        return super(RentalIncidentLog, self).create(vals_list)

    ticket_id = fields.Many2one('rental.operation.ticket', string='Thuộc Phiếu Vận Hành', ondelete='cascade')
    vehicle_ref = fields.Char(string='Mã Xe gặp vấn đề', required=True) 
    
    timing = fields.Selection([
        ('incident', 'Sự cố lúc đang thuê'),
        ('checkin', 'Phát hiện lúc trả xe')
    ], string='Thời điểm phát sinh', required=True, default='incident')

    date_reported = fields.Datetime(string='Ngày giờ ghi nhận', default=fields.Datetime.now)
    
    # Tiền tệ
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        default=lambda self: self.env.company.currency_id,
    )

    damage_description = fields.Text(string='Mô tả lỗi / Hư hỏng')
    cost = fields.Monetary(string='Chi phí đền bù (Tiền phạt)', default=0.0, currency_field='currency_id')
    is_paid = fields.Boolean(string='Đã thanh toán tiền phạt', default=False)

    fault_party = fields.Selection([
        ('customer', 'Lỗi do Khách hàng'),
        ('vehicle', 'Lỗi do Xe / Công ty')
    ], string='Lỗi thuộc về')

    customer_decision = fields.Selection([
        ('repair_wait', 'Khách đợi sửa'),
        ('replace_vehicle', 'Khách yêu cầu Đổi xe mới'),
        ('terminate_early', 'Khách trả xe (Chấm dứt sớm)')
    ], string='Hướng giải quyết (nếu là Sự cố)')

    status = fields.Selection([
        ('new', 'Mới'),
        ('processing', 'Đang xử lý'),
        ('resolved', 'Đã giải quyết')
    ], string='Trạng thái', default='new')

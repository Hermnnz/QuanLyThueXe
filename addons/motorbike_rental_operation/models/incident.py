# -*- coding: utf-8 -*-
from odoo import models, fields

class RentalIncidentLog(models.Model):
    _name = 'rental.operation.incident.log'
    _description = 'Nhật ký Sự cố & Hư hỏng'

    name = fields.Char(string='Mã Ghi nhận (Mã INC)', required=True, copy=False, readonly=True, default='Mới')
    ticket_id = fields.Many2one('rental.operation.ticket', string='Thuộc Phiếu Vận Hành', ondelete='cascade')
    vehicle_ref = fields.Char(string='Mã Xe gặp vấn đề', required=True) 
    
    timing = fields.Selection([
        ('incident', 'Sự cố lúc đang thuê'),
        ('checkin', 'Phát hiện lúc trả xe')
    ], string='Thời điểm phát sinh', required=True, default='incident')

    date_reported = fields.Datetime(string='Ngày giờ ghi nhận', default=fields.Datetime.now)
    
    damage_description = fields.Text(string='Mô tả lỗi / Hư hỏng')
    cost = fields.Float(string='Chi phí đền bù (Tiền phạt)')
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


class RentalVehicleReplacement(models.Model):
    _name = 'rental.operation.vehicle.replacement'
    _description = 'Phiếu Yêu cầu Đổi xe'

    name = fields.Char(string='Mã Đổi Xe (Mã REP)', required=True, copy=False, readonly=True, default='Mới')
    incident_id = fields.Many2one('rental.operation.incident.log', string='Thuộc Sự cố', ondelete='cascade')
    old_vehicle_ref = fields.Char(string='Xe cũ (Thu hồi)')
    new_vehicle_ref = fields.Char(string='Xe mới (Giao đi)')
    
    date_replaced = fields.Datetime(string='Ngày đổi', default=fields.Datetime.now)
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('done', 'Đã đổi xong')
    ], string='Trạng thái', default='draft')

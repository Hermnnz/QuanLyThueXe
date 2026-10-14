# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RentalVehicleReplacement(models.Model):
    _name = 'rental.operation.vehicle.replacement'
    _description = 'Phiếu Yêu cầu Đổi xe'

    name = fields.Char(string='Mã Đổi Xe (Mã REP)', required=True, copy=False, readonly=True, default='Mới')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Mới':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.operation.vehicle.replacement')
        return super(RentalVehicleReplacement, self).create(vals_list)

    incident_id = fields.Many2one('rental.operation.incident.log', string='Thuộc Sự cố', ondelete='cascade')
    old_vehicle_ref = fields.Char(string='Xe cũ (Thu hồi)')
    new_vehicle_ref = fields.Char(string='Xe mới (Giao đi)')
    
    date_replaced = fields.Datetime(string='Ngày đổi', default=fields.Datetime.now)
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('done', 'Đã đổi xong')
    ], string='Trạng thái', default='draft')

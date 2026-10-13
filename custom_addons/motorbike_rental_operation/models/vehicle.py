# -*- coding: utf-8 -*-
from odoo import models, fields

class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _description = 'Thông tin Xe (Đơn giản)'

    name = fields.Char(string='Tên xe', required=True)
    vehicle_code = fields.Char(string='Mã Xe', required=True)
    price = fields.Float(string='Giá tiền')

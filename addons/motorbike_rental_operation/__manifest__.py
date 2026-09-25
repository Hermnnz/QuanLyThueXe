# -*- coding: utf-8 -*-
{
    'name': 'Motorbike Rental Operations',
    'version': '1.0',
    'summary': 'Quản lý Giao nhận, Hậu kiểm, Sự cố và Đổi xe',
    'author': 'Giang',
    'depends': ['base'], # Thêm 'fleet', 'motorbike_rental_core' sau nếu cần
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}

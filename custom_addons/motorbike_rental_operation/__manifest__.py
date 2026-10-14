# -*- coding: utf-8 -*-
{
    'name': 'Vận Hành Thuê Xe Máy',
    'version': '1.0',
    'summary': 'Quản lý Giao nhận, Hậu kiểm, Sự cố và Đổi xe',
    'author': 'Giang',
    'license': 'LGPL-3',
    'depends': ['base', 'fleet', 'motorbike_rental_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/ticket_views.xml',
        'views/incident_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,


    'category': 'Quản trị',  # Hoặc 'Dịch vụ', 'Bán hàng' tùy nhóm bạn chọn

}

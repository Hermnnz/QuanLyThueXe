# -*- coding: utf-8 -*-
{
    'name': 'Vận Hành Thuê Xe Máy',
    'version': '1.0',
    'summary': 'Quản lý Giao nhận, Hậu kiểm, Sự cố và Đổi xe',
    'author': 'Giang',
    'depends': ['base'], # Thêm 'fleet', 'motorbike_rental_core' sau nếu cần
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/fleet.vehicle.csv',
        'views/ticket_views.xml',
        'views/incident_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,


    'category': 'Quản trị',  # Hoặc 'Dịch vụ', 'Bán hàng' tùy nhóm bạn chọn

}

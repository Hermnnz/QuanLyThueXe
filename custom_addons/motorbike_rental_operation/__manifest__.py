# -*- coding: utf-8 -*-
{
    'name': 'Vận Hành Thuê Xe Máy',
    'version': '1.0',
    'summary': 'Quản lý Giao nhận, Hậu kiểm và Sự cố',
    'author': 'Giang',
    'license': 'LGPL-3',
    'depends': ['base', 'fleet', 'motorbike_rental_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/price_catalog_data.xml',
        'views/price_catalog_views.xml',
        'views/confirm_wizard_views.xml',
        'views/ticket_views.xml',
        'views/incident_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'motorbike_rental_operation/static/src/css/operation.css',
        ],
    },
    'installable': True,
    'application': True,
    'category': 'Quản trị',
}

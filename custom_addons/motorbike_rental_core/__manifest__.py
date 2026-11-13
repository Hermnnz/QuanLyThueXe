{
    'name': 'Cho thuê xe',
    'version': '18.0.1.0.35',
    'summary': 'Quản lý khách hàng và hợp đồng thuê xe máy',
    'category': 'Services/Rental',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
        'fleet',
        'motorbike_fleet_management',
        'website',
    ],
    'data': [
        'security/rental_security.xml',
        'security/ir.model.access.csv',
        'data/rental_sequence_data.xml',
        'data/rental_booking_request_sequence.xml',
        'data/rental_extension_sequence.xml',
        'data/rental_vehicle_type_data.xml',
        'views/rental_vehicle_views.xml',
        'views/rental_contract_views.xml',
        'views/rental_extension_views.xml',
        'views/rental_booking_request_views.xml',
        'views/res_partner_views.xml',
        'views/website_contact_removal.xml',
        'views/website_rental_templates.xml',
    ],
    'assets': {  # Nạp widget chọn xe gia hạn vào giao diện quản trị Odoo.
        'web.assets_backend': [  # Chỉ giao diện nội bộ, không thêm mã vào website đặt xe.
            'motorbike_rental_core/static/src/js/extension_vehicle_selection.js',  # Dropdown có lựa chọn tất cả và từng xe.
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
}

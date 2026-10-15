{
    'name': 'Motorbike Rental Core',
    'version': '18.0.1.0.4',
    'summary': 'Quản lý khách hàng và hợp đồng thuê xe máy',
    'category': 'Services/Rental',
    'license': 'LGPL-3',
    'depends': ['base', 'contacts', 'fleet','motorbike_fleet_management'],
    'data': [
        'security/rental_security.xml',
        'security/ir.model.access.csv',
        'data/rental_sequence_data.xml',
        'views/rental_vehicle_views.xml',
        'views/rental_contract_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
}
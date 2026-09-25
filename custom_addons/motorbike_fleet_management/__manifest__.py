{
    'name': 'Motorbike Fleet & Maintenance',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Electric motorbike specifications and maintenance records',
    'description': 'Electric motorbike battery specifications and maintenance tracking for Odoo Fleet.',
    'license': 'LGPL-3',
    'depends': ['fleet'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/service_type.xml',
        'views/fleet_views.xml',
    ],
    'installable': True,
    'application': True,
}

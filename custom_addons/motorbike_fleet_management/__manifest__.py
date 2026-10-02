{
    'name': 'Motorbike Fleet & Maintenance',
    'version': '19.0.3.1.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Week 6: vehicle and maintenance List/Form with basic CRUD',
    'description': 'Minimal Fleet models, basic ACL and manually entered vehicle/maintenance records. No custom workflow or availability.',
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

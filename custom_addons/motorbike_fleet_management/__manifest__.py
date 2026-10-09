{
    'name': 'Motorbike Fleet & Maintenance',
    'version': '19.0.4.0.0',
    'category': 'Human Resources/Fleet',
    'summary': 'Week 7: Fleet search, Kanban, validation and maintenance workflow',
    'description': 'Minimal Fleet with core maintenance logic. No Rental/Inspection integration or availability API.',
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

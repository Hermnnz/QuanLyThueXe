{
    "name": "Motorbike Rental Finance",

    "version": "1.0.0",

    "summary": "Finance management for motorbike rental",

    "author": "Nguyen Duc Anh",

    "category": "Services/Rental",

    "depends": [
        "base",
        "account",
    ],

    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "views/price_catalog_views.xml",
        "views/rental_payment_views.xml",
        "views/rental_charge_views.xml",
        "views/finance_actions.xml",
        "views/finance_menu.xml",
        "data/finance_demo.xml",
    ],

    "installable": True,

    "application": True,

    "license": "LGPL-3",
}


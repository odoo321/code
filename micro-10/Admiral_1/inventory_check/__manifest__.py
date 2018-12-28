# -*- coding: utf-8 -*-
{
    "name": """Inventory Check""",
    "summary": """Inventory Check""",
    "category": "Equipment",
    "images": [],
    "version": "10.0",
    "application": False,

    "author": "Hashmicro / Duy",
    "website": "https://hashmicro.com",
    "license": "AGPL-3",
    "depends": [
        'stock','purchase','sale'
    ],
    "data": [
        "views/templates.xml",
        "views/inventory_check_view.xml",
    ],
    "qweb": ['static/src/xml/*.xml'],
    "auto_install": False,
    'application': True,
    "installable": True,
}
# -*- coding: utf-8 -*-
{
    'name': "hm_std_inventory",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Hashmicro/Vu/Krupesh",
    'website': "hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock_picking_wave','stock_account'],

    # always loaded
    'data': [
        'data/stock_data.xml',
        'views/templates.xml',
        'views/views.xml',
        'views/hide_menu.xml',
        'security/accsess_rules.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

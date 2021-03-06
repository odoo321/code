# -*- coding: utf-8 -*-
{
    'name': "Quickbooks Odoo Connector",

    'summary': """
        QuickBooks Odoo Connector """,

    'description': """
        Export and import data to and from Quickbooks
    """,

    'author': "Techspawn Solutions",
    'website': "http://www.techspawn.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'custom',
    'version': '2.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'connector', 'account', 'sale', 'account_accountant', 'stock', 'purchase'],
    'price': 149.00,
    'currency': 'EUR',

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'templates.xml',
        'views/backend.xml',
        'views/customer_vendor.xml',
        'views/product_quick.xml',
        'views/payment_term_view.xml',
        'views/quick_account.xml',
        'views/schedule_refresh_token.xml',
    ],
    'external_dependencies': {
        'python': ['requests_oauthlib'],
    },
    
    
}
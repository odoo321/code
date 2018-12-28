{
    'name': 'Full Accounting',
    'summary': """Install all the Accounting modules..""",
    'version': '10.0.1.0.0',
    'author': 'Hashmicro/Mustufa Kantawala',
    'website': "http://www.hashmicro.com",
    'company': 'Hashmicro',
    "category": "Acconting",
    'depends': [
        'account_accountant', 
        # 'sg_setup',
        'sg_update_taxcode',
        'account_deposit',
        'credit_debit_note',
        'sg_partner_payment',
        'sg_bank_reconcile',
        'sg_account_config',
        'sg_account_report',
        'sg_cashflow_report',
        'sales_bankcharges',
        'sg_account_standardisation',
        'enterprise_accounting_report',
        'account_multicurrency_revaluation',
    ],
    'data': [],
    'installable': True,
    'application': False,
}

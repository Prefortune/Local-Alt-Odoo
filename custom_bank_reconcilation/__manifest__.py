# -*- coding: utf-8 -*-

{
    'name': 'Custom Bank Reconciliation',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Custom module for bank reconciliation',
    'description': """
    Custom module for bank reconciliation
    """,
    'depends': ['account', 'account_accountant', 'web'],
    "data": [
        "security/ir.model.access.csv",
        "views/custom_bank_reconcilation_wizard_views.xml"
    ],
    'assets': {
        'web.assets_backend': [
            'custom_bank_reconcilation/static/src/**/*',
        ],
    },
    'license': 'OEEL-1',
}

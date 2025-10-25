# -*- coding: utf-8 -*-

{
    "name": "Tranzila Payment Acquirer",
    "summary": """Payment Acquirer: Payment Tranzila""",
    "description": """Tranzila Payment Acquirer""",
    "license": 'LGPL-3',
    "author": 'Lilach Gilliam',
    "website": "http://www.bizzup.app",
    "category": 'Accounting/Payment',
    "version": "18.0.1.0.2",
    "depends": [
        'lyg_payment',
        'account_payment',
        'website_payment',
    ],
    "data": [
        'data/payment_method_data.xml',
        'views/payment_provider_view.xml',
        'data/payment_provider_data.xml',
    ],
    "installable": True,
    "uninstall_hook": 'uninstall_hook',
}

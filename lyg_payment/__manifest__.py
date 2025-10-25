# -*- coding: utf-8 -*-

{
    "name": "LYG Payment",
    "summary": """Payment Provider: Payment Tranzila - Provider Information""",
    "description": """Tranzila Payment Provider : Stored Data of Payment Provider""",
    "license": 'LGPL-3',
    "author": 'Lilach Gilliam',
    "website": "http://www.bizzup.app",
    "category": 'Accounting/Payment',
    "version": '18.0.1.0.0',
     "depends": [
        'payment',
    ],
    "data": [
        'data/payment_provider_data.xml',

    ],
    "installable": True,
    'auto_install': True,
}

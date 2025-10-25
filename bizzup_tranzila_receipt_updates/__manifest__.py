# -*- coding: utf-8 -*-

{
    'name': 'Tranzila - LYG Receipt Updates',
    'summary': 'Customizations on Tranzila & LYG Receipt',
    "version": "18.0.1.1.5",
    'license': 'Other proprietary',
    'author': 'Lilach Gilliam',
    'website': 'https://bizzup.app',
    'depends': ['payment_tranzila', 'lyg_receipt', 'sale'],
    'data': {
        'views/account_invoice_view.xml',
        'views/payment_provider_view.xml',
        'views/sale_order_view.xml',
        'views/account_payment_view.xml',
        'views/account_receipt_view.xml',
    },
    'application': True,
    'installable': True,
}

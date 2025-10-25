{
    'name': 'Cardcom Payment Gateway',
    'version': '1.0',
    'category': 'Payment',
    'summary': 'Integration with Cardcom Low Profile payment gateway',
    'description': 'Integration with Cardcom Low Profile payment gateway for secure payments in Odoo',
    'depends': ['payment', 'account','sale'],
    'data': [
        'views/cardcom_provider_template.xml',
        'views/payment_provider_views.xml',
        'views/account_invoice_views.xml',
        'views/sale_order_form.xml',
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'application': False,
}

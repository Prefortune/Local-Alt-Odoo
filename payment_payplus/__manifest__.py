{
    'name': 'PayPlus Payment Gateway',
    'version': '1.0',
    'category': 'Payment',
    'summary': 'Integration with PayPlus payment gateway',
    'description': 'Integration with PayPlus payment gateway for secure payments in Odoo',
    'depends': ['payment', 'account', 'sale_management'],
    'data': [
        'views/payplus_provider_template.xml',
        'views/payment_provider_views.xml',
        'views/account_move.xml',
        'views/sale_order_view.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'application': False,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'assets': {
        'web.assets_frontend': [
            # 'payment_payplus/static/src/js/payplus_payment.js',
        ],
    },
}

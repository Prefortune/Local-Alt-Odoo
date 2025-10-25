# -*- coding: utf-8 -*-
{
    'name': 'POS Pay4All Payment Gateway',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'license': 'OPL-1',
    'summary': 'Complete Pay4All integration (e-Kwanza, Multicaixa Express) for Point of Sale',
    'description': '''
        Complete Pay4All payment integration for Odoo Point of Sale
        
        Features:
        • e-Kwanza mobile wallet payments
        • Multicaixa Express terminal payments  
        • 3 specialized screens with professional design
        • Robust validation for Angolan phone numbers
        • Real API integration with official endpoints
        • Intelligent timeouts per payment method
        • Modern interface following professional mockups
        • Full support for AOA (Angolan Kwanza)
        
        Ready for production use!
    ''',
    'author': 'Pay4All Development Team',
    'website': 'https://pay4all.ao',
    'support': 'suporte@pay4all.ao',
    'depends': ['point_of_sale', 'payment'],
    'data': [
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_pay4all/static/src/js/main.js',
            'pos_pay4all/static/src/js/pay4all_terminal.js',
            'pos_pay4all/static/src/js/pay4all_compat_simple.js',
            'pos_pay4all/static/src/js/pay4all_payment_screen.js',
            'pos_pay4all/static/src/js/pay4all_processing_screen.js',
            'pos_pay4all/static/src/js/pay4all_multicaixa_wait_screen.js',
            'pos_pay4all/static/src/js/pay4all_payment_interface.js',
            'pos_pay4all/static/src/css/pay4all_payment.css',
            'pos_pay4all/static/src/xml/pay4all_payment_screen.xml',
            'pos_pay4all/static/src/xml/pay4all_processing_screen.xml',
            'pos_pay4all/static/src/xml/pay4all_multicaixa_wait_screen.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}

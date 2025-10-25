{
    'name': 'Alt Split Deliveries',
    'version': '18.0.2.0',
    'category': 'Inventory/Delivery',
    'summary': 'Alt split delivery method for multiple addresses',
    'description': """
        This module adds a new delivery method called "Alt Split Deliveries" 
        that allows splitting orders to multiple delivery addresses.
        
        Features:
        - Alt split delivery method with alt_ prefix
        - Multiple delivery addresses per order
        - Hebrew support (פיצול כתובות)
        - Compatible with Odoo 18 standard delivery system
        - Replaces standard delivery method with custom split delivery
    """,
    'author': 'Alt Mobile Studio',
    'website': 'https://www.altmobilestudio.com',
    'depends': [
        'base',
        'sale',
        'delivery',
        'website_sale',
        'mail',
        'web',
        'sale_management',
        'report_xlsx'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'reports/xlsx_code.xml',
        'views/sale_order_views.xml',
        'views/sale_page_menu.xml',
        'views/alt_split_delivery_website_templates.xml',
        'data/split_delivery_data.xml',
        'views/view_delivery_carrier_form_inherit.xml',
        'views/delivery_form_templates_website.xml',
        'views/alt_split_delivery_portal_page.xml',
        'views/sale_order_portal_content_inherit.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_frontend': [
            '/alt_split_delivery/static/src/js/split_delivery_checkout.js',
            '/alt_split_delivery/static/src/js/split_delivery_portal.js',
            '/alt_split_delivery/static/src/js/set_delivery_date.js',
        ],
    },
} 
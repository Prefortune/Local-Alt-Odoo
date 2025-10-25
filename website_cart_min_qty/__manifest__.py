# -*- coding: utf-8 -*-
{
    'name': 'Cursor Website Cart Minimum Quantity',
    'version': '18.0.1.0.0',
    'summary': 'Set minimum quantity requirements for products in website cart',
    'description': """
        This module allows you to set minimum quantity requirements for products
        when customers add them to cart on the website. You can set different
        minimum quantities for different products.
        
        Features:
        - Set minimum quantity per product
        - Frontend validation with user-friendly messages
        - Backend validation for cart operations
        - Configurable minimum quantity settings
    """,
    'category': 'Website/Website',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'website',
        'website_sale',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'views/product_template_views.xml',
        'views/website_sale_views.xml',
        'views/cart_min_qty_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_cart_min_qty/static/src/js/cart_min_qty.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

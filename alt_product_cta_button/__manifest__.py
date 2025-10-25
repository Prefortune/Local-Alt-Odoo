{
    'name': 'alt Product CTA Button',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Customizes the Add to Cart button behavior on product pages',
    'description': 'Allows hiding, replacing, or appending a custom button like Contact Us',
    'depends': ['website', 'website_sale'],
    'data': [
        'views/product_cta_settings_view.xml',
        'views/product_cta_template.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_frontend': [
            'alt_product_cta_button/static/src/js/cta_behavior.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

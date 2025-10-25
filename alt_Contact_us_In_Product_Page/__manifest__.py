# -*- coding: utf-8 -*-
{
    'name': "Contact us In Product Page",

    'summary': "Contact us In Product Page",

    'description': """
Contact us In Product Page
    """,

    'author': "Prefortune Technologies LLP",
    'website': "https://www.prefortune.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'website_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_template.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    "assets": {
        "web.assets_frontend": [
            # "pf_mmbikes_customization/static/src/js/product_form.js",
        ],
    },
    'installable': True,
    'auto_install': False,
}

# -*- coding: utf-8 -*-
{
    'name': "Chika Customization",

    'summary': "Chika Customization",

    'description': """
Chika Customization
    """,

    'author': "Prefortune",
    'website': "https://www.prefortune.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale_management','product','stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product.xml',
        'views/pos_order.xml',
        'views/pos_order_mrp_button.xml',
        'wizard/pos_session_invoice_wizard.xml',
        'views/pos_session_invoice_button.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pf_chika_custom/static/src/js/pos_product_price_patch.js',
            #'pf_chika_custom/static/src/xml/pos_product_item.xml',
        ],
    },
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'installable': True,
    'application': True,
}


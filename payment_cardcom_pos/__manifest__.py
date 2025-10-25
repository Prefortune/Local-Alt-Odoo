# -*- coding: utf-8 -*-
{
    'name': "payment_cardcom_pos",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'payment', 'account', 'sale_management'],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    # always loaded
    'data': [
        'views/templates.xml',
        'views/views.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
        
    ],
}


# -*- coding: utf-8 -*-
{
    'name': "pf_guest_address",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','website_sale'],
    'data': [
        'views/views.xml',
    ],  
    'assets' : {
         'web.assets_frontend' : [
            '/pf_guest_address/static/src/js/set_delivert_address.js',
            '/pf_guest_address/static/src/js/set_guest_split.js',
         ]
    }
}

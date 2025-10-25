# -*- coding: utf-8 -*-
{
    'name': "pf_guest_address",
    'version': '0.1',

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'depends': ['base','website_sale'],
    'data': [
        'views/views.xml',
        'views/website.xml',

    ],  
    'assets' : {
         'web.assets_frontend' : [
            '/pf_guest_address/static/src/js/set_delivert_address.js',
            '/pf_guest_address/static/src/js/set_guest_split.js',
         ]
    }
}

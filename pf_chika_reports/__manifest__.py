# -*- coding: utf-8 -*-
{
    'name': "pf_chika_reports",

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
    'depends': ['base','account','sale_management','web','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/paper_format.xml',
        'views/external_layout.xml',
        'views/invoice_report.xml',
        'views/pro_forma_report.xml',
        'views/purchase_report.xml',
        'views/purchase_model.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
    'web.report_assets_common': [
        '/pf_chika_reports/static/src/css/style.css',
        ],
    },
}


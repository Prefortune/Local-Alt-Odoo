# -*- coding: utf-8 -*-
# Part of Prefortune.

{
    'name' : 'Sale Invoice Template',
    'version' : '17.0.0.1',
    'summary': '',
    'sequence': 10,
    'description': """Our all-inclusive CSV / Excel - Bulk Product Variant ImportOur Odoo app simplifies the process of importing products along with their variants directly from CSV or Excel files. With this module, you gain the flexibility to import custom fields as well. Seamlessly create or update both products and their variants with essential details like images, prices, quantities, and stock levels directly from your CSV or Excel files. Easily identify and manage products and variants with the 'Unique Identification' field. Simplify your product management workflow with our Odoo app today!""",    
    "depends": ['sale_management','account','sale','stock','purchase'],
    "application": True,
    
    # Author
    'author': 'Prefortune Technologies LLP',
    'website': 'http://www.prefortune.com/',
    'maintainer': 'Prefortune Technologies LLP',
    
    "data": [
        'report/ir_action_report.xml',
        'views/invoice_report.xml',
        'views/layout_template_inherit.xml',
        'views/sale_order_report.xml',
        'views/sale_order.xml',
        'views/account_move.xml',
        'views/report_picking_inherit.xml',
        'views/base_document_layout_view.xml',
        'views/report_deliveryslip.xml',
        'views/purhase_order_report.xml',
        # 'views/purchase_order_rfq_report.xml',  
        ],
    'assets': {
    'web.report_assets_common': [
        'pf_sale_invoice_template/static/src/css/style.css'
        ],
    },

    # "images": ["static/description/banner.png",],
    "installable": True,
    "auto_install": False,
    "application": True,
    'translation': True, 

}

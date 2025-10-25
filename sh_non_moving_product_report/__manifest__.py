# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Non-Moving Products Report",
    "author": "Softhealer Technologies",
    "website": "http://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Warehouse",
    "license": "OPL-1",
    "summary": "Advance Inventory Report Stock Aging Report For Unsold Products Report Unsold Product Report Non Moving Products Report Non-Moving Product Report Non Moving Product Report Inventory Analysis Report Non-Moving Stock Report Non Moving Stock Report With PDF Non Moving Stock Report With Excel Non Moving Stock Report With XLSX Odoo Non Selling Products Report Non Non Selling Inventory Reports Non Selling Stock Reports Non Moving Inventory Reports Non Moving Item Reports Unsold Inventory Reports Unsold Stock Reports Dead Stock Reports Deadstock Reports ",
    "description": "A non-moving products report is a document that shows a list of products in inventory that have not been sold or used within a specific time. This helps to optimize inventory levels, free up warehouse space, and improve cash flow.",
    "version": "0.0.2",
    "depends": ['base_setup', 'web', 'stock'],
    "application": True,
    "data": [
        'security/sh_non_moving_product_report_groups.xml',
        'security/ir.model.access.csv',
        'report/sh_non_moving_product_report_templates.xml',
        'views/sh_non_moving_product_views.xml',
        'wizard/sh_non_moving_product_report_wizard_views.xml',
    ],
    "auto_install": False,
    "installable": True,
    'images': ['static/description/background.png'],
    "price": 35,
    "currency": "EUR"

}

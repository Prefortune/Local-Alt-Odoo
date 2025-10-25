# -*- coding: utf-8 -*-
{
    'name': "LionWheel Delivery Method",

    'summary': "LionWheel API integration for delivery management",

    'description': """
LionWheel Delivery Method Module
================================

This module integrates Odoo with LionWheel API for delivery management.

Features:
- Create shipments through LionWheel API
- Check shipment status
- Generate shipment labels
- Manage delivery carriers with LionWheel configuration
- Support for daily routes and optimization
- Company management through LionWheel API
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Delivery',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'delivery'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/shipment_views.xml',
        'views/stock_picking_views.xml',
        'views/delivery_carrier_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}

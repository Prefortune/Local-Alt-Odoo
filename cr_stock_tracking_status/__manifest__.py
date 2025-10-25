# -*- coding: utf-8 -*-
# Part of Creyox Technologies
{
    "name": "Stock Tracking Status",
    "author": "Creyox Technologies",
    "website": "https://www.creyox.com",
    "support": "support@creyox.com",
    "category": "Inventory",
    "summary": "This module enhances financial control and refund validation in Odoo. It restricts credit note creation to only via Sales Orders and Invoices, and prevents posting of credit notes by regular users—only Accounting Managers can post them. It also disables converting regular invoices into credit notes. Additionally, in the Point of Sale (POS) interface, non-manager employees are required to enter a valid manager PIN before processing a refund, ensuring secure and authorized refund handling.",
    "license": "LGPL-3",
    "version": "18.1",
    "description": """ 
        """,
    "depends": [
        "base",
        "web",
         'stock','bizzup_stock_customization',
    ],
    "data": [
        'views/stock_picking_views.xml'

    ],
    'assets': {
        'web.assets_backend': [
            'cr_stock_tracking_status/static/src/**/*'
        ],
        },
    "installable": True,
    "auto_install": False,
    "application": True,
}
# -*- coding: utf-8 -*-
# Part of Creyox Technologies
{
    "name": "Stock Blind Receipt",
    "author": "Creyox Technologies",
    "website": "https://www.creyox.com",
    "support": "support@creyox.com",
    "category": "Extra Tools",
    "summary": ".",
    "license": "LGPL-3",
    "version": "18.0",
    "description": """ 
        """,
    "depends": [
        "base",
        "web",'stock','stock_barcode'
    ],
    "data": [
        'views/stock_picking_type.xml',
    ],
    'assets': {
        'web.assets_backend': [
                'cr_blind_receipt/static/src/**/*'
            ],
        },
    "installable": True,
    "auto_install": False,
    "application": True,
}
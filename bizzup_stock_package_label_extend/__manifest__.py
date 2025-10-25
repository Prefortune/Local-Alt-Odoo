# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Stock Package Label Extension",
    "version": '18.0.0.3.0',
    "summary": "Enhances package labels with customer details and package sequence",
    "description": "This module extends package labels in stock transfers by adding customer name, full delivery address, and package numbering (X of Y).",
    "author": "Your Name or Company",
    "website": "https://yourwebsite.com",
    "license": "LGPL-3",
    "category": "Inventory/Stock",
    "depends": ["stock"],
    "data": [
        "report/report_package_barcode.xml",
        "report/report_stock_picking_package_barcode.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'bizzup_stock_package_label_extend/static/src/js/barcode_picking.js',
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}

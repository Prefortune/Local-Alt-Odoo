# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "BizzUp Stock Orderpoint Restriction",
    "version": "18.0.0.6.0",
    "category": "Inventory/Stock",
    "summary": "Restricts stock warehouse orderpoints based on company settings and manages PO consignment status.",
    "description": """
        This module enforces restrictions on stock warehouse orderpoints when the main company is not set 
        as 'is_main=True'. It also automates the 'is_po_consig' field for purchase orders based on 
        consignment locations and ensures it remains read-only.
    """,
    "author": "BizzUp",
    "website": "https://www.bizzup.com",
    "license": "LGPL-3",
    "depends": ["stock", "purchase", "bizzup_stock_customization"],
    "data": [
        "views/purchase_order.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

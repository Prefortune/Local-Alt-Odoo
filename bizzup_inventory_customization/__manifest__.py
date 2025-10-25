# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Inventory Customization",
    "description": """
        HT01559
        Access to Inventory - MM.
    """,
    "version": "18.0.1.1.5",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "www.bizzup.app",
    "depends": ["stock" , "purchase", "bizzup_price_access_customization"],
    "demo": [],
    "data": [
        "security/price_access_security.xml",
        "views/stock_quant_views.xml",
        "views/purchase_order_views.xml",
    ],
    "installable": True,
    "application": False,
}

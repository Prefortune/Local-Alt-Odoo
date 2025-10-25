# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Direct Communication",
    "description":
        """
        Adds a Direct Communication workflow to vendor pricelists,
        purchase orders, and sales orders with company-based access control.
        """,
    "version": "18.0.1.2.0",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems",
    "website": "https://bizzup.app",
    "depends": ["purchase", "sale", "product", "bizzup_price_access_customization","bizzup_stock_customization"],
    "data": [
        "views/product_supplierinfo_view.xml",
        "views/purchase_order_view.xml",
        "views/sale_order_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}

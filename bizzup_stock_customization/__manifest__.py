# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Stock Customization",
    "description": """This module helps to add the customisation of consignment location in stock""",
    "version": "18.0.1.0.15",
    "license": "Other proprietary",
    "author":  "Gilliam Management Services and Information Systems",
    "website": "https://bizzup.app",
    "depends": ["sale_management", "stock", "purchase", "accountant"],
    "data": {
        "views/res_config_settings_view.xml",
        "views/purchase_order_view.xml",
        "views/res_partner_view.xml",
        "views/sale_order_view.xml",
        "views/stock_location_view.xml",
        "views/account_move_view.xml",
        "views/stock_picking_views.xml",
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
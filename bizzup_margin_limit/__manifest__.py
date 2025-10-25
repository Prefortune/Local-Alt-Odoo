# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Margin Limit",
    "description": """
        HT01568.
Use cases:

    Paramters in res.company
        For each company, add two new fields:
            Limit parameter
            Error parameter
        Only setting/manager user can set it
        If any field is bigger than 1, it will pop up an error but it allows the user to insert this number

    If a user  tries to approve a Sales Order or a POS Order, the following will happen:
        Profitability Warning:
            If the profit of the order is less than the total cost of products multiplied by (1 + field from 1.a.i),
            → the user will receivProfitability
        Profitability Block:
            If the profit of the order is less than the total cost of products multiplied by (1 + field from 1.a.ii),
            → the system will block the order from being approved.

        2.1. Manager Notification:
            If the user has an assigned manager,
            → the manager will receive a notification to approve the order.

        2.1.1. No Manager Assigned:
            If the user has no manager assigned,
            → the user will be allowed to approve the order themselves.

        2.2. POS Flow – Manager PIN Required:
            If the order is being placed in the POS,
            → the manager of the employee will need to enter their PIN code to approve the order.
        Zero Threshold Handling:
            If any of the thresholds (alert or block) is set to 0,
            → no warning or block will be triggered, respectively.
    """,
    "version": "18.0.1.0.4",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "www.bizzup.app",
    "depends": ["sale_management", "point_of_sale"],
    "demo": [],
    'data': {
        "security/ir.model.access.csv",
        "views/res_compnay_views.xml",
        "views/sale_order_views.xml",
        "wizard/margin_parameter_wizard_views.xml",
        "wizard/profit_approve_wizard.xml",
    },
    "assets": {
        "point_of_sale._assets_pos": [
            "bizzup_margin_limit/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
}

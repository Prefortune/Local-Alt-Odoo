# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Tranzila J5",
    "description": """
        US : HT01283
        Locil - Adding Tranzila - J5 option
          """,
    "version": "18.0.1.0.1",
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "depends": ["point_of_sale", "pos_online_payment", "payment_tranzila",],
    "data": {
        "views/res_config_views.xml",
        "views/pos_payment_views.xml",
        "views/payment_transaction_views.xml",
        "views/pos_order_views.xml",
    },
    "assets": {
        "point_of_sale._assets_pos": [
            "bizzup_tranzila_j5/static/src/**/*",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}

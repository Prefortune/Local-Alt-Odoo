# -*- coding: utf-8 -*-

{
    "name": "Bizzup POS Cash Limit",
    "summary": """This module show the warning in pos""",
    "description": """This module show the warning in pos screen if cash
                       amount exceeded""",
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "category": "POS/Payment",
    "version": "18.0.1.0.2",
    "depends": [
        "point_of_sale",
        "payment",
        "lyg_receipt"
    ],
    "data": [
        "views/pos_payment_method_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "bizzup_pos_cash_limit/static/src/**/*",
        ],
    },
    "installable": True,
}

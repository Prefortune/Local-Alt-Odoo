# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Obligo Customization",
    "summary": """This module will display the smart button in account move for obligo also in 'Delivery Slip' Report
                  name of packages will be displayed""",
    "description": """HT01649
1. I want to add in the button of the invoice the obligo of the partner
2. I want to add in the delivery slip the number of realted packages""",
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "category": "POS/Payment",
    "version": "18.0.1.0.3",
    "depends": [
        "bizzup_obligo",
        "account",
        "stock",
    ],
    "data": [
        "views/stock_picking_views.xml",
        "report/delivery_slip_report.xml",
        "report/invoice_report_views.xml",
    ],
    "installable": True,
}

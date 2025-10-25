# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Inventory Move Report",
    "summary": """This module will allow to filter Products which are not  been moved to a customer location 
    (i.e., destination location of type 'customer') """,
    "description": """HT01689""",
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "category": "POS/Payment",
    "version": "18.0.1.1.5",
    "depends": [
        "stock",
    ],
    "data": [
        "views/stock_move_line_views.xml",
    ],
    "installable": True,
}

# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    'name': 'Bizzup Purchase Cutomization',
    "description": """ HT01859 | Field Remain to Receive in PO line and analysis report. """,
    "version": "18.0.1.0.2",
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "depends": ['purchase'],
    "data": {
        "views/purchase_order_line_views.xml",
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}

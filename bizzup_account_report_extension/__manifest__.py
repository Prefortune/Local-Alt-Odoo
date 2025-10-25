# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Account Report Extension",
    "description": """
        Custom extension for Partner Ledger and Account Move Line reporting in Bizzup.
    """,
    "version": "18.0.0.1.0",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "https://bizzup.app",
    "depends": ["account_reports"],
    "data": [
        "views/partner_ledger.xml",
    ],
    "application": False,
    "installable": True,
}

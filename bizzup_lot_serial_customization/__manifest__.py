# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Lot Serial Customization",
    "description": """"This module customizes the stock lot functionality to
     ensure proper handling of unique lot constraints and default
     company settings.""",
    "version": "18.0.1.0.0",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems",
    "website": "https://bizzup.app",
    "depends": ["stock", "sale_management", "purchase"],
    "data": {
        "views/res_config_settings_view.xml",
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}

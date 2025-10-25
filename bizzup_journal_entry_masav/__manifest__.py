# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    'name': 'Bizzup Journal Entry for Masav',
    'summary': 'Bizzup Journal Entry for Masav',
    "description": """
     User Story : HT01743
     This module enhances the vendor payment process in Odoo by introducing 
     custom logic for managing journal entries related to Masav processing
        """,
    "category": "Accounting/Localizations",
    'version': '18.0.1.0.2',
    'license': 'Other proprietary',
    'author': 'Gilliam Management Services and Information Systems, Ltd.',
    'website': 'https://bizzup.app',
    'depends': [
        'vander_bill_ascii_report',
        'account',
    ],
    'data': [
        'views/account_payment_views.xml',
        'wizard/res_config_settings_views.xml',
        'data/ir_actions_server_data.xml',
        'data/account_account_tag_data.xml',
    ],
    'application': True,
    'installable': True,
}

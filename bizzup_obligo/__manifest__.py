# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    'name': 'Partner Credit Management',
    'version': "18.0.0.14.0",
    'summary': 'Manage credit limit, obligo, and postponed checks for partners',
    'description': """
        Adds credit tolerance to Accounting Settings.
        Computes obligo as credit + postponed checks.
        Prevents approvals when limits exceeded.
    """,
    'category': 'Accounting',
    'depends': ['base', 'account', 'sale_management', 'sale_purchase_inter_company_rules'],
    'data': [
        'report/ir_actions_report.xml',
        'report/partner_credit_limit_report.xml',
        'views/res_config_settings.xml',
        'views/res_partner.xml',
        'views/excel_report_action.xml',
        'views/res_company_view.xml'
        # Add other view or data files here (e.g., security, menu items, etc.)
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

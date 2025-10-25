# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Margin Limit",
    "description": """
        HT01644.
        
        Approval consigment po in sub company will not approval

If the in the company that the SO is creating the synchronized documents should be validate so for PO consigment are will not be 

It should be a new boolean in comapny settings
    """,
    "version": "18.0.1.0.1",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "www.bizzup.app",
    "depends": ["sale_management",'sale_stock',
        'purchase_stock',
        'sale_purchase_inter_company_rules'],
    "demo": [],
    'data': {
        "views/res_compnay_views.xml",
    },
    "installable": True,
    "application": False,
}

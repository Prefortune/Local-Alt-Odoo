# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Landing Cost",
    "summary": """This module allows to restrict the price and product based 
    on the company""",
    "description": """HT01573
    As a user of the import management system,
I want to manage an "Import File" as a central entity that contains all relevant information for the import process — including stock transfers, multiple batches, invoices, costs, and additional data —
so that I can have a single point of reference and track progress via a project task.
Acceptance Criteria:

    It is possible to create a new Import File with a unique ID, description, and status.
    The Import File can include multiple stock transfers.
    The Import File can include multiple batches.
    Relevant invoices (purchase, customs, cost loading) can be linked to the Import File.
    Additional import-related fields can be filled, such as arrival date, supplier, container number, etc.
    The Import File will be represented as a task in a project for progress tracking and activity logging. """,
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "category": "POS/Payment",
    "version": "18.0.1.0.1",
    "depends": [
        "bizzup_import_case",
        "project",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/landing_cost_wizard_views.xml",
        "report/landing_cost_report.xml",
        "views/project_task_views.xml",
    ],
    "installable": True,
}

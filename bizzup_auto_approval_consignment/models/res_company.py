# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api,fields, models, _


class ResCompany(models.Model):
    """Inherited Res Company for adding a new field"""
    _inherit = "res.company"

    synchronised_document = fields.Boolean("Synchronised Document Restrict")

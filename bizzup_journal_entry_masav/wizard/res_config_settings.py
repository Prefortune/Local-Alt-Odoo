# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    entry_for_payments_after_masav = fields.Boolean(
        string='Entry for Payments After Masav',
        config_parameter='bizzup_journal_entry_masav.entry_for_payments_after_masav',
        help='If enabled, Masav journal entries will be created for payments when printing the report.')
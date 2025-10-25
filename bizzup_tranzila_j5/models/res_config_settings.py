# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    enable_j5_tranzila = fields.Boolean(
        string="Enable J5 for Tranzila",
        help="Activate J5 functionality for POS and ERP when using Tranzila.",
    )

    @api.model
    def get_values(self):
        """
        Load stored values from all active pos.config records into res.config.settings.
        If multiple POS configs exist, and values differ, settings may reflect the first match only,
        but all configs are considered for updates.
        """
        res = super(ResConfigSettings, self).get_values()

        pos_configs = self.env['pos.config'].search([
            ('company_id', '=', self.env.company.id),
            ('active', '=', True)
        ])

        # For example, if enable_j5_tranzila needs to be True if ANY pos.config has it enabled
        enable_j5_tranzila = any(config.enable_j5_tranzila for config in pos_configs)

        res.update(
            enable_j5_tranzila=enable_j5_tranzila
        )

        return res

    def set_values(self):
        """Save the value from res.config.settings into pos.config"""
        super(ResConfigSettings,self).set_values()
        pos_config = self.env['pos.config'].search([('company_id', '=', self.env.company.id),('active','=',True)])  # Get POS config
        if pos_config:
            for pos in pos_config:
                pos.enable_j5_tranzila = self.enable_j5_tranzila


class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_j5_tranzila = fields.Boolean(
        string="Enable J5 for Tranzila",
        help="Activate J5 functionality for POS and ERP when using Tranzila."
    )

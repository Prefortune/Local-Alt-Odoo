# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    credit_tolerance = fields.Integer(
        string="Tolerance for Credit Limit (in days)",
        config_parameter="bizzup_obligo.credit_tolerance"
    )

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'bizzup_obligo.credit_tolerance',
            str(self.credit_tolerance)
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            credit_tolerance=int(
                float(
                    self.env['ir.config_parameter'].sudo().get_param('bizzup_obligo.credit_tolerance', default=0)
                )
            )
        )
        return res

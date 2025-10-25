# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api,fields, models, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    limit_parameter = fields.Float("Limit Parameter")
    error_parameter = fields.Float("Error Parameter")

    @api.onchange('limit_parameter','error_parameter')
    def _onchange_parameters(self):
        """
        Show a warning if a parameter is greater than 1.
        Only users with settings/manager access can modify these parameters.
        """
        if not self.env.user.has_group('base.group_system'):  # 'Settings' group
            raise UserError(
                _(
                    "You do not have permission to change these parameters."
                    )
                )

        if self.limit_parameter > 1 or self.error_parameter > 1:
            return {
                'warning': {
                    'title': _("Parameter Update"),
                    'message': _(
                        "You are about to change the parameter. Do you want to proceed?"
                        ),
                }
            }

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        add pos payment method field to pos
        """
        fields = super()._load_pos_data_fields(config_id)
        fields += [
            "limit_parameter",
            "error_parameter",
        ]
        return fields

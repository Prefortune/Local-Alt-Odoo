# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, _
from odoo.exceptions import ValidationError


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        """
            Allows only authorized users to apply inventory adjustments.
            Returns:
                super: Calls the parent method if the user has the necessary permissions.
            Raises:
                ValidationError: If a user without proper permissions attempts an inventory adjustment.
        """
        if report_ref == 'stock.report_inventory':
            if not self.env.user.has_group(
                    'bizzup_inventory_customization.group_allow_inventory_adjustment'
                    ):
                raise ValidationError(
                    _(
                        'You have no Access to Print Count Sheet Report.'
                    )
                )
        res = super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)
        return res

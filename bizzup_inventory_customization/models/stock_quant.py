# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    cost_gap = fields.Float(
        string=_("Cost Gap"),
        compute="_compute_cost_gap", store=True
    )

    @api.depends("inventory_diff_quantity", "value", "quantity")
    def _compute_cost_gap(self):
        """
        Computes the cost gap for each record.

        New formula:
            cost_gap = (value / quantity) * inventory_diff_quantity

        Handles both positive and negative inventory differences.
        If quantity is 0 (to avoid division by zero), cost_gap is set to 0.0.
        """
        for rec in self:
            if rec.quantity:
                rec.cost_gap = (rec.value / rec.quantity) * rec.inventory_diff_quantity
            else:
                rec.cost_gap = 0.0

    def action_apply_inventory(self):
        """
            Allows only authorized users to apply inventory adjustments.

            Returns:
                super: Calls the parent method if the user has the necessary permissions.

            Raises:
                ValidationError: If a user without proper permissions attempts an inventory adjustment.
        """
        if not self.env.user.has_group('bizzup_inventory_customization.group_allow_inventory_adjustment'):
            raise ValidationError(
                _(
                    'You are not allowed to Access Inventory Adjustment.'
                )
            )
        return super().action_apply_inventory()

# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    """Inherited StockLocation"""

    _inherit = "stock.location"

    consignation_locations = fields.Boolean("Is Consignation location")

    @api.constrains("consignation_locations")
    def _check_consignation_locations(self):
        """
        Ensures only one location per company can be marked as a consignation
        location.Raises a `ValidationError` if another location in the
        same company is marked.
        """
        for record in self:
            # Check if another location in the same company is marked
            # as consignation
            stock_location = self.env["stock.location"].search(
                [
                    ("company_id", "=", self.env.company.id),
                    ("id", "!=", record.id),
                    ("consignation_locations", "=", True),
                ],
                limit=1,
            )
            if stock_location and self.consignation_locations:
                raise ValidationError(
                    "Only one consignation location can be set to" " True per company."
                )

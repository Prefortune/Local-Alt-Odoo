# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, api


class StockLot(models.Model):
    """
    Inherits 'stock.lot' model to customize default values, onchange behavior,
    and constraints for stock lot records.
    """

    _inherit = "stock.lot"

    def default_get(self, fields_list):
        """
        Override default_get to ensure that the 'company_id' field is set
        to the current company when creating a new stock lot.
        """
        defaults = super().default_get(fields_list)
        company_id = self.env.company.id
        if company_id:
            defaults["company_id"] = company_id
        return defaults

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """
        Ensure the company_id is updated to match the current company
        when the product_id field is changed.
        """
        company_id = self.env.company.id
        self.company_id = company_id

    @api.constrains("name", "product_id", "company_id")
    def _check_unique_lot(self):
        """
        Enforce uniqueness constraint on lot name, product, and company,
        unless the constraint check is explicitly disabled via configuration.
        """
        disable_check = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "bizzup_lot_serial_customization.disable_unique_lot_check")
        )
        if disable_check:
            return True
        super()._check_unique_lot()

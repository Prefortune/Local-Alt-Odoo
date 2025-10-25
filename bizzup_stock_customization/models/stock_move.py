# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    real_demand = fields.Float(compute='_compute_real_demand', store=True, default=0.0)

    @api.depends('product_uom_qty')
    def _compute_real_demand(self):
        """ Compute the field real_demand, which is the product_uom_qty of the move """
        for move in self:
            # If the real_demand is not set, set it to the product_uom_qty
            if not move.real_demand:
                move.real_demand = move.product_uom_qty

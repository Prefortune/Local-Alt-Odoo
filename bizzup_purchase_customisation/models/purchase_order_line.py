# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api
from odoo.tools import SQL


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    remain_to_receive = fields.Float(
        string='Remain to Receive', readonly=True,
        help="Difference between ordered quantity and received quantity (can be negative)"
    )

    def _select(self):
        """
        Extends the parent _select method to include a computed remain_to_receive
        as (qty_received - product_qty) to reflect accurate quantities in pivot view.
        Negative values are preserved.
        """
        select_query = super()._select()
        additional_field = SQL(
            ", SUM(COALESCE(l.qty_received, 0.0) - COALESCE(l.product_qty, 0.0))::numeric AS remain_to_receive"
        )
        return SQL("%s %s", select_query, additional_field)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    remain_to_receive = fields.Float(
        string='Remain to Receive',
        compute='_compute_remain_to_receive',
        readonly=True,
        help="Difference between ordered quantity and received quantity (can be negative)"
    )

    def _compute_remain_to_receive(self):
        """ Computes the remaining quantity to receive for each purchase order line. """
        for line in self:
            line.remain_to_receive = line.qty_received - line.product_qty

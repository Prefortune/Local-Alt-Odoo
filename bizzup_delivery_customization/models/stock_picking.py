# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    """Inherited Stock Picking"""
    _inherit = "stock.picking"

    def unlink(self):
        """
        Override the unlink method to restrict the deletion of delivery orders
        with an assigned sequence number.
        """
        for picking in self:
            # Check if the picking type is 'outgoing' and the record has
            # a name (sequence number)
            if picking.picking_type_id.code == "outgoing" and picking.name:
                raise UserError(
                    _(
                        "You cannot delete a delivery order with a sequence"
                        " number: %s."
                    )
                    % picking.name
                )
        return super().unlink()

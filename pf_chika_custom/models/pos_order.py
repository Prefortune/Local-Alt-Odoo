from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)



class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _create_order_picking(self):
        #_logger.info("Creating picking for order %s", self.name)
        """Create a picking for the order."""
        res = super()._create_order_picking()

        # "In Odoo 17, when a stock picking is created from a POS order, how can we pass the customer note from each POS order line to the corresponding stock picking move line's description field?
        # we have akready picking_ids field in pos.order model
        for order in self:
            if order.picking_ids:
                for move in order.picking_ids.move_ids:
                    # Find the corresponding order line
                    order_line = order.lines.filtered(lambda l: l.product_id == move.product_id)
                    if order_line:
                        # Set the description to the customer note from the order line
                        move.description_picking = order_line.customer_note or ''
                        _logger.info("Set description for move %s to '%s'", move.name, move.description_picking)
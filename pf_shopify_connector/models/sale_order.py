from odoo import api, fields, models, _
import base64
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class ShopifySaleOrder(models.Model):
    _inherit = 'sale.order'

    shopify_order_id = fields.Char(string="Shopify Order Id")
    shopify_store = fields.Many2one('shopify.connector', string="Shopify Store")
    is_shopify_order = fields.Boolean(string="Shopify Order")
    generate_manufacture_order = fields.Boolean(string="Manufacture Order",default=False)

    def action_confirm(self):
        """Override action_confirm to check stock and create MO if needed."""
        res = super(ShopifySaleOrder, self).action_confirm()
        self.create_manufacture_order()
        return res

    def create_manufacture_order(self):
        # Loop through each order line
        for order in self:
            for line in order.order_line:
                product = line.product_id
                _logger.info("Manufacture product: %s", product.name)
                # Check if the product is 'storable' and requires manufacturing
                if product.type == 'product':
                    _logger.info("Manufacture storabale product: %s", product.name)
                    qty_available = product.qty_available
                    qty_needed = line.product_uom_qty
                    
                    if qty_needed > qty_available:
                        qty_to_produce = qty_needed - qty_available  # Calculate shortage
                        
                        # Create Manufacturing Order (MO)
                        mo_vals = {
                            'product_id': product.id,
                            'product_qty': qty_to_produce,
                            'product_uom_id': product.uom_id.id,
                            'bom_id': product.bom_ids[:1].id if product.bom_ids else False,  # Use first BOM if exists
                            'origin': order.name,  # Link MO to Sale Order
                        }
                        mo = self.env['mrp.production'].sudo().create(mo_vals)

                        # Confirm the MO to start production automatically
                        # mo.action_confirm()
                        # mo.action_assign()  # Reserve components if available
                        # mo.button_mark_done()  # Mark MO as done to finish production
                        order.generate_manufacture_order = True
                        order.message_post(body=f"MO {mo.name} created for {product.display_name} (Qty: {qty_to_produce})")
    
    def ordered_delivered(self):
        for order in self:
            pickings = order.picking_ids.sorted(key=lambda p: p.id)  # sort by ID
            _logger.info("All pickings (by ID): %s", pickings)

            for picking in pickings:
                _logger.info("Processing picking %s with state %s", picking.name, picking.state)
                if picking.state == 'draft':
                    picking.action_confirm()
                    _logger.info("(draft) Picking state %s", picking.state)
                if picking.state == 'confirmed':
                    picking.action_assign()
                    _logger.info("(confirmed) Picking state %s", picking.state)
                if picking.state == 'assigned':
                    for move_line in picking.move_line_ids:
                        if not move_line.quantity:
                            move_line.quantity = move_line.product_uom_qty
                    picking.button_validate()
                    _logger.info("(assigned) Picking state %s", picking.state)
        # for order in self:
        #     done_picking = order.picking_ids.filtered(lambda p: p.state == "confirmed")
        #     _logger.info("done_picking %s", done_picking)
        #     if done_picking:
        #         _logger.info("done_picking %s", done_picking)
        #         # done_picking.action_assign()
        #         # done_picking.button_validate()
        #     else:
        #         assigned_picking = order.picking_ids.filtered(lambda p: p.state == "assigned")
        #         _logger.info("assigned_picking %s", assigned_picking)
        #         if assigned_picking:
        #             assigned_picking.button_validate()

    def action_open_manufacturing_orders(self):
        """Open Manufacturing Orders based on the Sale Order origin."""
        self.ensure_one()
        return {
            'name': 'Manufacturing Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('origin', '=', self.name)],  # Filter by origin (Sale Order name)
            'context': dict(self.env.context),
        }


class ShopifySaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    shopify_order_line_id = fields.Char(string="Shopify Order Line Id")
    discount = fields.Float(string='Discount (%)', default=0.0, digits=(100, 99))
    discount_amount = fields.Float(string='Discount Amount', default=0.0)

class ShopifyCouponProgram(models.Model):
    _inherit = 'loyalty.program'

    shopify_coupon_id = fields.Char(string="Shopify Coupon Id")
    shopify_store = fields.Many2one('shopify.connector', string="Shopify Store")
    is_shopify_coupon = fields.Boolean(string="Shopify Coupon")


class ShopifyAccountMove(models.Model):
    _inherit = 'account.move'

    def remove_invoice(self):
        _logger.info("this is remove invoice")
        for record in self:
            record.with_context(force_delete=True).unlink()


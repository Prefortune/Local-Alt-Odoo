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
    sale_order_tag = fields.Many2one('pf.order.tag', string="Order tag")
    order_notes = fields.Text(string="Notes")

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


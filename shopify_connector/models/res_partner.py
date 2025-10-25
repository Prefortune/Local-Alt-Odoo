from odoo import api, fields, models, _
import base64
from odoo.exceptions import ValidationError

class ShopifyResPartner(models.Model):
    _inherit = "res.partner"

    shopify_customer_id = fields.Char(string="Shopify Customer Id")
    shopify_address_id = fields.Char(string="Shopify Address Id")
    shopify_store = fields.Many2one('shopify.connector', string="Shopify Store")
    is_shopify_customer = fields.Boolean(string="Shopify Customer")
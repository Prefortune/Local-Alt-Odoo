
from odoo import models, fields

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    pf_alt_products = fields.Many2many(
        'product.product', 'pf_table_alt_products', string='Alternative Products', domain="[('available_in_pos', '=', True)]")
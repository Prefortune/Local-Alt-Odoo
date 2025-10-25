from odoo import models, fields, api, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    alt_supports_split_delivery = fields.Boolean(
        string='תומך בפיצול משלוח', 
        default=False,
        help='האם המוצר הזה יכול להתפצל למנות משלוח שונות'
    )

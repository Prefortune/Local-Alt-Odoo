from odoo import api, fields, models

class CommonFields(models.AbstractModel):
    _name = 'pf.cart.common.field'
    _description = 'Cart Common Quantity Fields'

    pf_min_cart_qty = fields.Integer(string='Minimum Cart Quantity', default=1)
    pf_max_cart_qty = fields.Integer(string='Maximum Cart Quantity', default=10)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    # _description = 'Extended Product Template with Cart Fields'
    pf_min_cart_qty = fields.Integer(string='Minimum Cart Quantity', default=1)
    set_website_product_qty = fields.One2many('set.website.product.qty' , 'product_id')


class ProductVariants(models.Model):
    _inherit = 'product.product'
    # _description = 'Extended Product Variants with Cart Fields'
    pf_min_cart_qty = fields.Integer(string='Minimum Cart Quantity', default=1)


class SetWebSiteProductQty(models.Model):
    _name = 'set.website.product.qty'

    website_id = fields.Many2one('website',string="Select WebSite")
    pf_min_cart_qty = fields.Integer(sttring="Set Min Qty")
    product_id = fields.Many2one('product.template')


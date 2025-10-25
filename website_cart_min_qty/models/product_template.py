# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    website_min_qty = fields.Integer(
        string='Website Minimum Quantity',
        default=1,
        help='Minimum quantity required when adding this product to cart on website'
    )
    website_min_qty_enabled = fields.Boolean(
        string='Enable Minimum Quantity',
        default=False,
        help='Enable minimum quantity validation for this product on website'
    )

    @api.model
    def get_website_min_qty(self, product_id):
        """Get minimum quantity for a product on website"""
        product = self.browse(product_id)
        if product.website_min_qty_enabled:
            return product.website_min_qty
        return 1

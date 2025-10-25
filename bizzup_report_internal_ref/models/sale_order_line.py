# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Add a computed field for product description
    product_description = fields.Char('Product Description', compute='_compute_remove_internal_ref',)

    def _compute_remove_internal_ref(self):
        for line in self:
            # Check if there's a default_code (internal reference) for the product
            if line.product_id and line.product_id.default_code:
                internal_ref = line.product_id.default_code

                if internal_ref in line.name:

                    cleaned_name = line.name.replace(internal_ref,'').strip()

                    cleaned_name = cleaned_name.replace(
                        '[','').replace(']','').strip()

                    line.product_description = cleaned_name
                else:
                    line.product_description = line.name
            else:
                line.product_description = line.name

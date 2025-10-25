# -*- coding: utf-8 -*-
from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    check_variant = fields.Boolean('Check Variant', compute='_check_default_code')

    def _check_default_code(self):
        for product in self:
            if product.attribute_line_ids:
                product.check_variant = False
            else:
                product.check_variant = True

# -*- coding: utf-8 -*-
from odoo import models, fields

class Website(models.Model):
    _inherit = 'website'

    pf_cart_min_qty_enabled = fields.Boolean(
        string='Enforce Minimum Cart Quantity',
        default=False,
        help='Enable minimum cart quantity enforcement on website checkout.'
    )
    pf_cart_min_qty_value = fields.Integer(
        string='Minimum Cart Quantity',
        default=30,
        help='Minimum total quantity required in cart to proceed to checkout.'
    )

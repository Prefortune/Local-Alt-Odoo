# -*- coding: utf-8 -*-

from odoo import models, fields


class Website(models.Model):
    _inherit = 'website'

    global_min_qty_enabled = fields.Boolean(
        string='Enable Global Minimum Quantity',
        default=False,
        help='Enable global minimum quantity validation for all products'
    )
    global_min_qty = fields.Integer(
        string='Global Minimum Quantity',
        default=1,
        help='Global minimum quantity required for all products on website'
    )

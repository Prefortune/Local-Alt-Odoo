# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    global_min_qty_enabled = fields.Boolean(
        string='Enable Global Minimum Quantity',
        related='website_id.global_min_qty_enabled',
        readonly=False,
        help='Enable global minimum quantity validation for all products'
    )
    global_min_qty = fields.Integer(
        string='Global Minimum Quantity',
        related='website_id.global_min_qty',
        readonly=False,
        help='Global minimum quantity required for all products on website'
    )

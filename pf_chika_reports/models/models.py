# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    reference_no = fields.Char(string='Reference')
    lpo_number = fields.Char(string='LPO Number')

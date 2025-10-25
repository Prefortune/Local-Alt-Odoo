# -*- coding: utf-8 -*-

from odoo import api, models, fields

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    npay = fields.Char('Number of Payments', store=True)
    fpay = fields.Char('First Pay',store=True)
    spay = fields.Char('Second Pay',store=True)
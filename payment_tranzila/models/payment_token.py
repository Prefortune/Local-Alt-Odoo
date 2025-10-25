# -*- coding: utf-8 -*-

from odoo import _, fields, models


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    ccno = fields.Char("Credit Card Number", help="Stored only last four digit for re-use in next transaction")
    expyear = fields.Char("Expiration Year")
    expmonth = fields.Char("Expiration Month")

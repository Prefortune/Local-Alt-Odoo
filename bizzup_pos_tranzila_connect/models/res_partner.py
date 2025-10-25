# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request


class PaymentTransaction(models.Model):
    _inherit = "res.partner"

    def get_partner_vat(self, amount, customer):
        """While Creating Payment From POS and Payment Method
           is EMV, This method will call to check before
           processing payment, The total amount of order is greater
           than the limit amount for vat in setting.
           Ticket - HT01506"""
        customer = self.env['res.partner'].browse(customer)
        icpsudo = self.env['ir.config_parameter'].sudo()
        vat_limit = icpsudo.get_param(
            "l10n_il_lyg.vat_limit"
        )
        if customer and not customer.vat and int(amount) > int(vat_limit):
            return False
        else :
            return True

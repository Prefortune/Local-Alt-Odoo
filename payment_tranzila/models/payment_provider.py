# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _

TIMEOUT = 60


class PaymentProviderTranzila(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('tranzila', 'Tranzila')], ondelete={'tranzila': 'set default'})
    supplier = fields.Char('Supplier')
    TranzilaPW = fields.Char("Tranzila Password")
    token_supplier = fields.Char('Token Supplier')
    token_tranzilaPW = fields.Char('Tranzila Token Password')

    def _get_default_payment_method_id(self, code):
        self.ensure_one()
        if self.code != 'tranzila':
            return super()._get_default_payment_method_id(code)
        return self.env.ref('payment_tranzila.payment_method_tranzila').id

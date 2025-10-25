# -*- coding: utf-8 -*-

from odoo import models,api


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        res.pos_order_id.transaction_id = res.id
        return res

    def get_number_of_installment(self):
        """
        get transaction of pos order
        """
        transaction = self.search([], limit=1, order="id desc")

        npay = transaction.npay
        return npay

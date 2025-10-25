# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosPaymentPMethod(models.Model):
    _inherit = "pos.payment.method"

    is_cash_method = fields.Boolean("Cash Limit Warning")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        add pos payment method field to pos
        """
        fields = super()._load_pos_data_fields(config_id)
        fields += ["is_cash_method"]
        return fields

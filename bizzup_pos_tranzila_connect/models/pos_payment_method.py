# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosPaymentPMethod(models.Model):
    _inherit = "pos.payment.method"

    is_pos_physical_terminal = fields.Boolean(
        "Pos Physical Terminal", store=True, default=False
    )
    tranzila_terminal_ids = fields.One2many(
        "tranzila.physical.terminal", "payment_method_id"
    )
    payment_limit = fields.Integer("Payment Limit")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        add pos payment method field to pos
        """
        fields = super()._load_pos_data_fields(config_id)
        fields += [
            "is_pos_physical_terminal",
            "tranzila_terminal_ids",
            "payment_limit",
            "online_payment_provider_ids",
        ]
        return fields

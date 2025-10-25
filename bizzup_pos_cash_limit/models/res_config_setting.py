# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_cash_payment_limit = fields.Integer(
        string="POS Cash payment Limit",
        config_parameter="bizzup_pos_cash_limit.pos_cash_payment_limit",
    )

    @api.model
    def get_pos_cash_payment_limit(self):
        cash_payment_limit = (
            self.env["ir.config_parameter"]
            .sudo().get_param("bizzup_pos_cash_limit.pos_cash_payment_limit")
        )
        if cash_payment_limit:
            return cash_payment_limit

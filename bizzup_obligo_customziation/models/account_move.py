# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup),
# 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact: lg@bizzup.app

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    partner_obligo_balance = fields.Monetary(
        string="Partner Obligo Balance",
        compute="_compute_partner_obligo_balance",
        currency_field='currency_id'
    )
    partner_amount_due = fields.Monetary(
        string="Partner Amount Due",
    )

    def _compute_partner_obligo_balance(self):
        """
        Compute method to set the obligo balance and total amount due
        for the partner associated with the stock move.

        - `partner_obligo_balance`: Taken from the partner's `obligo` field.
        - `partner_amount_due`: Taken from the partner's `total_due` field.
        """
        for move in self:
            move.partner_obligo_balance = move.partner_id.obligo if move.partner_id.obligo else 0.0
            move.partner_amount_due = move.partner_id.total_due if move.partner_id.total_due else 0.0

    def action_view_partner_ledger(self):
        """
        Placeholder method for an action that will open the partner ledger view.
        Should be implemented to return an action dict showing partner accounting entries.
        """
        pass

# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, _
from odoo.tools import float_is_zero, float_compare, convert, plaintext2html

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = "pos.session"

    transaction_id = fields.Many2one(
        "payment.transaction", string="Payment Transaction"
    )

    def _loader_params_physical_machine(self):
        return {"search_params": {"domain": [], "fields": ["pos_id"]}}

    def _get_pos_ui_physical_machine(self, params):
        return self.env["tranzila.physical.terminal"].search_read(
            **params["search_params"]
        )

    def _create_split_account_payment(self, payment, amounts):
        payment_method = payment.payment_method_id
        if not payment_method.journal_id:
            return self.env['account.move.line']
        outstanding_account = payment_method.outstanding_account_id
        accounting_partner = self.env["res.partner"]._find_accounting_partner(payment.partner_id)
        destination_account = accounting_partner.property_account_receivable_id

        if float_compare(amounts['amount'], 0, precision_rounding=self.currency_id.rounding) < 0:
            # revert the accounts because account.payment doesn't accept negative amount.
            outstanding_account, destination_account = destination_account, outstanding_account
        if self.transaction_id:
            payment = self.transaction_id.payment_id
            account_payment = self.env['account.payment'].create({
                'amount': abs(amounts['amount']),
                'partner_id': payment.partner_id.id,
                'journal_id': payment_method.journal_id.id,
                'force_outstanding_account_id': outstanding_account.id,
                'destination_account_id': destination_account.id,
                'memo': _('%(payment_method)s POS payment of %(partner)s in %(session)s', payment_method=payment_method.name, partner=payment.partner_id.display_name, session=self.name),
                'pos_payment_method_id': payment_method.id,
                'pos_session_id': self.id,
            })
            final_payment = payment if payment else account_payment
            final_payment.action_post()
            return final_payment.move_id.line_ids.filtered(
            lambda
                line: line.account_id == accounting_partner.property_account_receivable_id
            )
        else:
            account_payment = self.env['account.payment'].create(
                {
                    'amount': abs(
                        amounts['amount']
                        ),
                    'partner_id': payment.partner_id.id,
                    'journal_id': payment_method.journal_id.id,
                    'force_outstanding_account_id': outstanding_account.id,
                    'destination_account_id': destination_account.id,
                    'memo': _(
                        '%(payment_method)s POS payment of %(partner)s in %(session)s',
                        payment_method=payment_method.name,
                        partner=payment.partner_id.display_name,
                        session=self.name
                        ),
                    'pos_payment_method_id': payment_method.id,
                    'pos_session_id': self.id,
                }
            )
            account_payment.action_post()
            return account_payment.move_id.line_ids.filtered(lambda line: line.account_id == accounting_partner.property_account_receivable_id)

# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    transaction_id = fields.Many2one(
        "payment.transaction", string="Payment Transaction"
    )


    def link_transaction_to_pos_order(self, session_id, order):
        """
        this method help to link transaction to pos order
        """
        session = self.env["pos.session"].browse(session_id)
        transaction = session.transaction_id
        if transaction:
            pos_order = self.env["pos.order"].browse(order)
            pos_order.transaction_id = transaction.id
            pos_order.transaction_id.pos_order_id = pos_order.id
            if not pos_order.to_invoice:
                pos_order.transaction_id._create_payment()

            account_move = pos_order.account_move
            if account_move and account_move.move_type == 'out_invoice':
                for transaction in pos_order.transaction_id:
                    _logger.info("\n\n -------transaction------- :\n%s",
                                 transaction)
                    _logger.info("\n\n -------transaction payment------- :\n%s",
                                 transaction.payment_id)
                    transaction.invoice_ids = [(4, account_move.id)]
                    if not transaction.payment_id:
                        transaction._create_payment()
                    else:
                        return order

    def _generate_pos_order_invoice(self):
        """This method is overridden for refund payment via physical terminal
           machine"""
        moves = self.env['account.move']

        for order in self:
            # Force company for all SUPERUSER_ID action
            if order.account_move:
                moves += order.account_move
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            # --- Step 1: Create Invoice ---
            move_vals = order._prepare_invoice_vals()
            new_move = order._create_invoice(move_vals)

            # --- Step 2: Process Refund Invoice and Credit Receipt Logic ---
            if new_move.move_type == 'out_refund':
                invoice_id = new_move.reversed_entry_id
                payment = self.env['account.payment'].search(
                    [('invoice_ids', '=', invoice_id.id)]
                )

                if payment and payment.receipt_id:
                    receipt = payment.receipt_id[0]
                    receipt_dict = receipt.action_post_credit_receipt()
                    credit_receipt = self.env['lyg.account.receipt'].browse(receipt_dict.get('res_id'))

                    credit_receipt.receipt_line_ids.update({'amount': abs(int(order.amount_paid))})
                    credit_receipt.action_post_receipt()

                    wizard_model = self.env['account.payment.wizard']
                    to_reconcile = []

                    # Handle batches for multiple lines
                    batches = wizard_model._get_payment_lines_credit_receipt()
                    new_batches = []
                    for batch in batches:
                        for line in batch["lines"]:
                            new_batches.append({**batch, "lines": line})
                    batches = new_batches
                    to_reconcile = [b["lines"] for b in batches]

                    pay_dict = {}

                    # Post each line
                    for line in credit_receipt.receipt_line_ids.filtered(lambda l: l.type == "invoice"):
                        line.write({"state": "post"})
                        amount = line.amount
                        if self.company_id.withholding_tax_process and line.withholding_amount:
                            amount -= line.withholding_amount

                        payment_vals = {
                            "date": credit_receipt.date,
                            "amount": abs(int(order.amount_paid)),
                            "payment_type": "outbound",
                            "partner_type": "customer",
                            "memo": line.invoice_id.name,
                            "currency_id": invoice_id.currency_id.id,
                            "journal_id": line.journal_id.id,
                            "partner_id": credit_receipt.partner_id.id,
                            "receipt_id": credit_receipt.id,
                            "means_of_payment": line.means_of_payment or False,
                        }

                        # Write-off
                        pay_line = wizard_model.invoice_receipt_line_ids.filtered(
                            lambda l: l.payment_difference_handling == "reconcile" and l.invoice_id == line.invoice_id
                        )
                        if pay_line:
                            last_line = sorted(
                                credit_receipt.receipt_line_ids.filtered(
                                    lambda inv: inv.invoice_id == pay_line.invoice_id)
                            )
                            if last_line and line.id == last_line[-1].id:
                                payment_vals['write_off_line_vals'] = [{
                                    'name': pay_line.write_off_label,
                                    'amount_currency': pay_line.payment_diff,
                                    'account_id': pay_line.write_off_account_id.id,
                                    'balance': pay_line.payment_diff,
                                }]

                        # Withholding tax
                        if self.company_id.withholding_tax_process and line.withholding_amount:
                            payment_vals["withholding_line_vals"] = {
                                "name": "Withholding Payment",
                                "amount": line.withholding_amount,
                                "account_id": self.company_id.cust_withholding_tax_account_id.id,
                                "withholding_tax_process": True,
                            }
                            payment_vals.update({"withholding_payment": True})

                        payment_record = self.env["account.payment"].create([payment_vals])
                        pay_dict[payment_record] = list(
                            filter(lambda l: l.move_id.name == payment_record.memo, to_reconcile))

                        # Force payment state
                        line.invoice_id.line_ids.remove_move_reconcile()
                        if line.type == "invoice" and line.invoice_id:
                            line.invoice_id.payment_state = "paid"

                    # --- Step 3: Reconcile Payments ---
                    for payment_obj, lines in pay_dict.items():
                        payment_obj.action_post()
                        domain = [
                            ("account_type", "in", ("asset_receivable", "liability_payable")),
                            ("reconciled", "=", False),
                        ]
                        payment_lines = payment_obj.move_id.line_ids.filtered_domain(domain)
                        payment_obj.name = payment_obj.move_id.name

                        for account in payment_lines.account_id:
                            for pay_line in payment_lines:
                                credit_payment = self.env["account.payment"].search([("memo", "=", pay_line.ref)])
                                credit_payments = credit_receipt.normal_receipt.payment_ids

                                (payment_lines + credit_payment.move_id.line_ids).filtered_domain([
                                    ("account_id", "=", account.id),
                                    ("reconciled", "=", False),
                                ]).with_context(credit_receipt=True).reconcile()

                                for pay in credit_payment:
                                    if not pay.is_reconciled:
                                        for line in credit_receipt.normal_receipt.receipt_line_ids.filtered(
                                                lambda l: l.type == "invoice"):
                                            (line.invoice_id.line_ids + pay.move_id.line_ids).filtered_domain([
                                                ("account_id", "=", account.id),
                                                ("reconciled", "=", False),
                                            ]).with_context(credit_receipt=True).reconcile()

                    # Finalize credit receipt
                    if all([line.state == "post" for line in credit_receipt.receipt_line_ids]):
                        if credit_receipt.name == _("New"):
                            credit_receipt.name = credit_receipt.env["ir.sequence"].next_by_code(
                                "lyg.account.receipt") or _("New")
                        credit_receipt.write({"state": "post"})

            # --- Step 4: Finalize Invoice Posting and Payment Handling ---
            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            new_move.sudo().with_company(order.company_id).with_context(skip_invoice_sync=True)._post()

            moves += new_move
            payment_moves = order._apply_invoice_payments(order.session_id.state == 'closed')

            if self.env.context.get('generate_pdf', True):
                new_move.with_context(skip_invoice_sync=True)._generate_and_send()

            if order.session_id.state == 'closed':
                order._create_misc_reversal_move(payment_moves)

        # --- Step 5: Return Invoice Form View ---
        if not moves:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': moves.ids[0],
        }

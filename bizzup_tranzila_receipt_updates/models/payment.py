#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import fields, models, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    ccno = fields.Char('Credit Card Number', store=True)
    approved_number = fields.Char('Credit Card Number', store=True)
    is_installment = fields.Boolean()
    npay = fields.Char('Number of installment', store=True)
    fpay = fields.Char('First Pay', store=True)
    spay = fields.Char('Second', store=True)

    def _create_payment(self, **extra_create_values):
        if self.provider_id.is_payment and self.provider_id.payment_mode == 'multiple' and (
                self.invoice_ids.payment_limit or self.sale_order_ids.payment_limit):
            if self.provider_id.is_payment:
                template_id = self.env.ref(
                    'lyg_receipt.lyg_mail_template_receipt')
                if self._context and not self._context.get('lastcall'):
                    if self.company_id.account_fiscal_country_id.code == 'IL':
                        name = self.env['ir.sequence'].next_by_code(
                            'lyg.account.receipt') or _('New')
                        rec_vals = {}
                        for rec in self.invoice_ids:
                            if self.provider_id.is_payment and self.provider_id.payment_mode == 'multiple':
                                rec_vals = {
                                    'name': name,
                                    'receipt_user_id': False,
                                    'partner_id': rec.partner_id.id if rec else
                                    self.partner_id.id,
                                    'company_id': self.company_id.id,
                                    'date': self.create_date,
                                    'currency_id': rec.currency_id.id if rec else self.company_id.currency_id.id,
                                    'subject': "תשלום מקוון",
                                    'receipt_line_ids':
                                        [(0, 0,
                                          {
                                              'journal_id': self.provider_id.journal_id.id,
                                              'type': 'invoice' if rec else 'generic',
                                              'invoice_id': rec.id if rec else None,
                                              'invoice_amount': rec.amount_residual if rec.amount_residual else 0.0,
                                              'amount': self.fpay,
                                              'credit_account_no': self.ccno,
                                              'voucher_check_no': self.approved_number,
                                              'tranzila_npay': self.npay,
                                              'tranzila_fpay': self.fpay,
                                              'tranzila_spay': self.spay,
                                              'means_of_payment': '3'})]
                                }
                                line_ids = []
                                for num in range(int(self.npay)):
                                    if num == 0:
                                        continue
                                    line_ids.append((0, 0,
                                                     {
                                                         'journal_id': self.provider_id.journal_id.id,
                                                         'type': 'invoice' if rec else 'generic',
                                                         'invoice_id': rec.id if rec else None,
                                                         'invoice_amount': rec.amount_residual if rec.amount_residual else 0.0,
                                                         'amount': self.spay,
                                                         'credit_account_no': self.ccno,
                                                         'voucher_check_no': self.approved_number,
                                                         'tranzila_npay': self.npay,
                                                         'tranzila_fpay': self.fpay,
                                                         'tranzila_spay': self.spay,
                                                         'tranzila_line_no': num,
                                                         'means_of_payment': '3'}))
                                rec_vals['receipt_line_ids'] += line_ids
                            else:
                                rec_vals = {
                                    'name': name,
                                    'receipt_user_id': False,
                                    'partner_id': rec.partner_id.id if rec else
                                    self.partner_id.id,
                                    'company_id': self.company_id.id,
                                    'date': self.create_date,
                                    'currency_id': rec.currency_id.id if rec else self.company_id.currency_id.id,
                                    'subject': "תשלום מקוון",
                                    'receipt_line_ids':
                                        [(0, 0,
                                          {
                                              'journal_id': self.provider_id.journal_id.id,
                                              'type': 'invoice' if rec else 'generic',
                                              'invoice_id': rec.id if rec else None,
                                              'invoice_amount': rec.amount_residual if rec.amount_residual else 0.0,
                                              'amount': self.amount,
                                              'credit_account_no': self.ccno,
                                              'voucher_check_no': self.approved_number,
                                              'tranzila_npay': self.npay,
                                              'tranzila_fpay': self.fpay,
                                              'tranzila_spay': self.spay,
                                              'means_of_payment': '3'})]
                                }
                        receipt_id = self.env['lyg.account.receipt'].with_context(
                            wizard_payment=True).create(rec_vals)
                        for receipt_line in receipt_id.receipt_line_ids:
                            current_invoice_lines = receipt_line.filtered(
                                lambda rl: rl.invoice_id.id == rec.id)
                            _logger.info(
                                "\n\n -------invoice_amount------- :\n%s",
                                current_invoice_lines.invoice_amount,
                            )
                        receipt_id.with_context(
                            receipt_active_id=receipt_id.id).action_post_receipt()
                        if receipt_id.state == 'draft':
                            self.env[
                                'account.payment.wizard'].action_create_payment()
                        for payment in receipt_id.payment_ids:
                            self.payment_id = payment.id
                            self.payment_id.npay = self.npay
                            self.payment_id.fpay = self.fpay
                            self.payment_id.spay = self.spay
                        if receipt_id.company_id.send_an_email_receipts and (
                                not self.company_id._fields.get(
                                    'is_tranzila_document',
                                    False) or not self.company_id._fields.get(
                            'is_greeninvoice_document',
                            False) or not self.company_id._fields.get(
                            'is_i4u_document', False)):
                            template_id.sudo().with_user(SUPERUSER_ID).send_mail(
                                receipt_id.id, force_send=True)
        else:
            res = super(PaymentTransaction, self)._create_payment()
            return res

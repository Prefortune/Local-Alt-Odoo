# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

import requests
import pprint
import logging
from odoo import models, fields
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_j5_transaction = fields.Boolean('Is J5 Transaction')
    transaction_mode = fields.Char('Transaction Mode')
    j5_with_token = fields.Boolean('J5 Transaction with Token')

    def create_j5_payment(self):
        """
        Processes a payment using the Tranzila payment provider for the current POS order.

        This method performs the following:
        - Retrieves the payment token for the customer.
        - Ensures that a transaction is linked to the order and is still pending.
        - Sends a payment request to the Tranzila API with the relevant credentials and token.
        - Handles the API response, checking for success or failure.
        - If successful:
            - Registers the payment in POS.
            - Creates an invoice for the order.
            - Links the invoice and payment to the original transaction.
            - Finalizes the POS order (sets it as invoiced).
        - If unsuccessful:
            - Marks the payment as failed on the related invoice.
            - Raises a ValidationError with the error message returned by Tranzila.

        Raises:
            ValidationError: If no transaction is linked to the order.
            ValidationError: If no token is found for the customer.
            ValidationError: If the Tranzila API returns an error response.
        """
        provider = self.env.ref(
            'lyg_payment.payment_provider_tranzila'
        ).id
        token = self.env['payment.token'].search(
            [
                ('partner_id', '=', self.partner_id.id)],
            limit=1
        )
        transaction = self.transaction_id
        if not transaction:
            raise ValidationError('There is no Transaction Linked to Current Order')
        if not token:
            raise ValidationError('There is no Token Found for the Customer of Current Order')
        if token and transaction.state == 'pending':
            api_url = 'https://secure5.tranzila.com/cgi-bin/tranzila71u.cgi'
            _logger.info(
                "\n\n ------- Api Url ------- :\n%s",
                api_url
                )
            headersList = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            payload = {
                'supplier': token.provider_id.token_supplier,
                'TranzilaPW': token.provider_id.token_tranzilaPW,
                'TranzilaTK': token.provider_ref,
                'sum': self.amount_total,
                "tranmode": "F",
                'expdate': token.expmonth + token.expyear,
                'reference': transaction.reference,
                'response_return_format': 'json'
            }
            response = requests.request(
                "POST",
                api_url,
                data=payload,
                headers=headersList
                )
            feedback_data = {
                'response': response.json()
            }
            _logger.info(
                "\n\n ------- Feedback Data -------- :\n%s",
                feedback_data
            )
            _logger.info(
                "entering _handle_feedback_data with data:\n%s",
                pprint.pformat(
                    feedback_data
                    )
            )
            response_from_traznila = feedback_data['response']
            if response_from_traznila.get(
                    'Response'
                    ) != '000':
                _logger.info(
                    "\n\n ------- Param Dict With Error Message -------- :\n%s",
                    feedback_data
                )
                self.account_move.payment_failed = True
                self.account_move.failure_message = response_from_traznila.get(
                    'error_msg'
                    )
                raise ValidationError(response_from_traznila.get('error_msg'))
            if self.account_move.transaction_ids.state == 'done' and self.account_move.payment_failed:
                self.account_move.payment_failed = False
            if response_from_traznila.get('Response') == '000':
                init_data = self.read()[0]
                payment_method = self.env['pos.payment.method'].browse(
                    init_data['online_payment_method_id'][0]
                    )
                self.add_payment(
                    {
                        'pos_order_id': self.id,
                        'amount': self._get_rounded_amount(
                            init_data['amount_total'],
                            payment_method.is_cash_count or not self.config_id.only_round_cash_method
                            ),
                        'payment_method_id': init_data['online_payment_method_id'][0],
                    }
                )
                this_products_line = []
                for rec in self.lines:
                    price = rec.price_unit if rec.price_unit else rec.unit_price
                    rec_list = [0, 0, {
                        'product_id': rec.product_id.id,
                        'name': rec.product_id.name,
                        'quantity': rec.qty,
                        'price_unit': price,
                    }]
                    this_products_line.append(
                        rec_list
                    )
                invoice = self.env['account.move'].create(
                    {
                        'move_type': 'out_invoice',
                        'date': fields.Date.today(),
                        'invoice_date': fields.Date.today(),
                        'state': 'draft',
                        'journal_id': 22,
                        'partner_id': self.partner_id.id,
                        'currency_id': self.partner_id.currency_id.id,
                        'invoice_line_ids': this_products_line,
                    }
                )
                invoice.action_post()
                self.account_move = invoice.id
                transaction.invoice_ids = [(4, self.account_move.id)]
                transaction.state = 'done'
                payment = transaction._create_payment()
                transaction.payment_id = payment.id
                self._process_saved_order(False)
                session = self.session_id
                self.name = session.config_id.sequence_id._next()
                self.state = 'invoiced'
            else:
                raise ValidationError(response_from_traznila.get('error_msg'))

    def set_partner_online_order(self,partner_id,order_id):
        """
        Assigns a customer (partner) to a POS order.

        This method sets the specified partner as the customer on the given POS order.
        It is typically used when an online order is placed and the customer needs to be
        linked to the corresponding POS order.

        Args:
            partner_id (int): The ID of the customer (res.partner).
            order_id (int): The ID of the POS order (pos.order).

        Returns:
            int: The ID of the updated POS order.
        """
        customer = self.env['res.partner'].browse(partner_id)
        pos_order = self.env['pos.order'].browse(order_id)
        if pos_order:
            pos_order.partner_id = customer.id
        return order_id

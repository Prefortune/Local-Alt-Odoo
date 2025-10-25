# -*- coding: utf-8 -*-

import logging
import math
import requests
from odoo import api, models, _, fields
from odoo.exceptions import ValidationError
from random import randint
_logger = logging.getLogger(__name__)


class PosPaymentP(models.Model):
    _inherit = "pos.payment"


    @api.model_create_multi
    def create(self, vals):
        """
        link pos transaction to payment
        """
        payment = super().create(vals)
        if payment.pos_order_id.transaction_id:
            payment.transaction_id = payment.pos_order_id.transaction_id
        return payment

    def _calculate_exact_rounded_payments(self, total_amount, num_payments):
        """ Ensures the first installment is adjusted so that all payments are whole numbers """
        if num_payments > 0:
            first_payment = math.ceil(total_amount / num_payments)
            print()
            while True:
                remaining_amount = total_amount - first_payment
                remaining_payment = remaining_amount / (num_payments - 1)

                # If the remaining payment is a whole number, we are done
                if remaining_payment == int(remaining_payment):
                    break

                # Increase the first payment and retry
                first_payment += 1

            return first_payment, int(remaining_payment)

    @api.model
    def get_pos_data(
            self, selected_limit, selected_terminal, amount, selected_partner,
            session, name
    ):
        """
        this method creates a transaction and links it to pos session
        """
        returnFeedback = False
        session = self.env["pos.session"].browse(session)
        amount_to_charge = int(amount)
        payment_limit = int(selected_limit)
        if selected_partner == "null":
            partner = self.env.user.partner_id
        else:
            partner = self.env["res.partner"].browse(int(selected_partner))
        terminal = self.env["tranzila.physical.terminal"].browse(
            int(selected_terminal))
        api_url = terminal.url
        if not terminal:
            raise ValidationError(
                _("You cannot pay without selecting the POS ID."))
        if amount_to_charge == 0:
            raise ValidationError(
                _("The value of the payment amount must be positive.")
            )
        headersList = {"Content-Type": "application/json",
                       "Connection": "keep-alive"}
        if payment_limit > 1:
            fpay, spay = self._calculate_exact_rounded_payments(amount_to_charge, payment_limit)
        else:
            fpay, spay = amount_to_charge, 0
        try:
            if amount_to_charge < 0:
                returnFeedback = True
                payload = {
                    "pos_id": terminal.pos_id,
                    "currency": "376",
                    "cred_type": "1",
                    "supplier": terminal.provider_id.supplier,
                    "tranmode": "C",
                    "sum": abs(amount_to_charge)
                }
            elif payment_limit:
                # below logic is for npay - 1 which
                # creates proper installments in tranzila API.
                payload = {
                    "pos_id": terminal.pos_id,
                    "currency": "376",
                    "cred_type": "8",
                    "npay": payment_limit - 1,
                    "fpay": fpay,
                    "spay": spay,
                    "supplier": terminal.provider_id.supplier,
                    "tranmode": "A",
                    "sum": amount_to_charge
                }
            else:
                payload = {
                    "pos_id": terminal.pos_id,
                    "currency": "376",
                    "cred_type": "1",
                    "supplier": terminal.provider_id.supplier,
                    "tranmode": "A",
                    "sum": amount_to_charge
                }
            response = requests.request(
                "POST", api_url, json=payload, headers=headersList
            )
            feedback_data = response.json()
            feedback = feedback_data
            _logger.info("\n\n -------payload------- :\n%s",
                         payload)
            _logger.info("\n\n -------response------- :\n%s",
                         feedback_data)
            transaction_result = (
                feedback_data.get("transaction_result")
                if feedback_data.get("transaction_result")
                else ""
            )
            if not amount_to_charge < 0:
                if (transaction_result and transaction_result.get(
                        "statusCode") == 0):
                    payment_method_id = self.env.ref(
                        "bizzup_pos_tranzila_connect.pos_payment_method_2"
                    )
                    partner_id = partner.id
                    # Ensure unique name for the transaction
                    old_name = name
                    if '/' in old_name:  # Check if the old name contains `/`
                        # Generate a random name in the format 'Order XXXX-XXX-XXXX'
                        unique_name = f"Order {randint(1000, 9999)}-{randint(100, 999)}-{randint(1000, 9999)}"
                    else:
                        unique_name = old_name
                    counter = 1
                    # Ensure the name is unique in the payment.transaction model
                    while self.env["payment.transaction"].search_count(
                            [("reference", "=", unique_name)],
                            limit=1
                    ):
                        if '/' in old_name:
                            # Generate another random name if it's still not unique
                            unique_name = f"Order {randint(1000, 9999)}-{randint(100, 999)}-{randint(1000, 9999)}"
                        else:
                            unique_name = f"{old_name}+{counter}"  # Append a counter to the original name
                            counter += 1

                    card_number = transaction_result.get("cardNumber")
                    approved_number = next(
                        (line.get("fieldValue") for line in
                         transaction_result.get("customerReceipt", []) if
                         line.get("fieldName") == "אישור מנפיק"), '')
                    transaction = self.env["payment.transaction"].create(
                        {
                            "reference": unique_name,
                            "amount": amount_to_charge,
                            "partner_id": (
                                partner_id if partner_id else
                                self.env.user.partner_id.id
                            ),
                            "approved_number":approved_number,
                            "ccno":card_number,
                            "payment_method_id": payment_method_id.id,
                            "provider_id": terminal.provider_id.id,
                            "provider_reference": feedback_data.get("index"),
                            "currency_id": self.env.company.currency_id.id,
                            "operation": "online_direct",
                            "npay": payment_limit,
                            "fpay": fpay,
                            "spay": spay,
                            "is_installment": True if int(
                                payment_limit) > 0 else False,
                        }
                    )
                    if transaction:
                        session.transaction_id = transaction.id
                        transaction.update({"state": "done"})
                        transaction.partner_id = partner.id
                else:
                    return feedback_data
            else:
                if returnFeedback:
                    return feedback
                return False
        except Exception as e:
            raise ValidationError(e)

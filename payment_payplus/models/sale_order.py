from math import log
import re
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError,UserError
import logging
_logger = logging.getLogger(__name__)
import json

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    is_warning_div = fields.Boolean(string="Warning Div")
    transaction_count = fields.Integer(string="Transaction Count", compute="_compute_transaction_count")
    transaction_number = fields.Char(string="Transaction Number")
    payplus_payment_status = fields.Selection([
      ('not_paid','Not Paid'), ('in_payment','In Payment'), ('paid','Paid')],
      string="Payplus Payment Status",
      compute="_compute_payplus_payment_status",
      store=True)
    is_j5_order_paid = fields.Boolean(string="Flag For J5 Order Paid",default=False)
    
    def action_payplus_refund(self):
        if len(self) > 1:
            raise UserError("Please select only one Sale Order to refund via PayPlus.")
        _logger.info("--- action_payplus_refund --- %s",self)
        res = self
        if res.state != 'sale' or not res.transaction_number:
            raise UserError("This Sale Order Is Not Confirm Or Not Payplus Order Or Not Payplus Paid Order.")
        
        transaction_table = self.env['payment.transaction'].search([(
            'sale_order_ids' , '=' , self.id
        )])[0]

        is_j5_payment_and_paid = False
        is_charge_and_paid = False
        if transaction_table:
            json_response = json.loads(transaction_table.payplus_payment_success_response_json) if isinstance(transaction_table.payplus_payment_success_response_json, str) else transaction_table.payplus_payment_success_response_json
            if json_response:
                type = json_response['type']
                if type == 'Approval':
                    is_j5_payment_and_paid = True
                else:
                    is_charge_and_paid = True

        if not is_charge_and_paid and not is_j5_payment_and_paid:
            raise UserError(" is not j5 order .")

        if is_j5_payment_and_paid and not self.is_j5_order_paid :
            raise UserError("J5 Order Is Not Confirm First Confirm Then Refund.")
        
        transaction_uid = res.transaction_number
        amount = res.amount_total
        payment_provider_id = transaction_table.provider_id
        _logger.info("--- payment_provider_id --- %s , %s",payment_provider_id , payment_provider_id.name)
        if payment_provider_id:
            if payment_provider_id.state == 'test':
                    api_key = payment_provider_id.test_api_key
                    secret_key = payment_provider_id.test_secret_key
                    url = 'https://restapidev.payplus.co.il/api/v1.0/'

            elif payment_provider_id.state == 'enabled':
                    api_key = payment_provider_id.production_api_key
                    secret_key = payment_provider_id.production_secret_key
                    url = 'https://restapi.payplus.co.il/api/v1.0/'
                    # url = 'https://restapidev.payplus.co.il/api/v1.0/'
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": api_key,
                "secret-key": secret_key
            }
            payload = {
                "transaction_uid": transaction_uid,
                "amount": amount,
            }
            _logger.info("header: %s", headers)
            _logger.info("payload: %s", payload)
            response = requests.post(f"{url}Transactions/RefundByTransactionUID", json=payload, headers=headers)
            response.raise_for_status() 
            result = response.json()
            description = result.get('results').get('description')
            _logger.info("Refund response: %s", result)
            if result and result['results']['status'] == 'success':
                # number = result.get('data').get('transaction').get('number')
                refund_transaction_id = result['data']['transaction']['uid']
                if refund_transaction_id:
                    # res.transaction_number = refund_transaction_id
                    res.message_post(body=f'PayPlus - The amount of {amount} has been refunded successfully. Transaction Number - {res.transaction_number}')
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Information!',
                            'message': f'Payplus Refund Amount of {amount} successful.',
                            'type': 'success', 
                            'sticky': False    
                        }
                    }

            else:
                raise UserError(f"Refund failed Something went wrong This is Already Refund Please Check In Payplus: {description}")
    
    def approve_j5_order(self):
        _logger.info("--- approve_j5_order --- called for SO %s", self.name)
        # transaction_ids = self.env['payment.transaction'].search([('sale_order_ids', '=', self.id)])
        transaction_ids = self.transaction_ids and self.transaction_ids[0] or None
        _logger.info("Found %s transactions for SO %s", len(transaction_ids), self.name)

        if transaction_ids:
            json_response = json.loads(transaction_ids.payplus_payment_success_response_json) if isinstance(transaction_ids.payplus_payment_success_response_json, str) else transaction_ids.payplus_payment_success_response_json
            payplus_payment_success_response_json = json_response
            _logger.info("Transaction response JSON: %s", payplus_payment_success_response_json)

            if payplus_payment_success_response_json:
                transaction_uid = payplus_payment_success_response_json.get('transaction_uid')
                transaction_type = payplus_payment_success_response_json.get('type')
                _logger.info("Transaction UID: %s | Type: %s", transaction_uid, transaction_type)

                if transaction_uid and transaction_type == 'Approval':
                    if transaction_ids.provider_id.state == 'test':
                        api_key = transaction_ids.provider_id.test_api_key
                        secret_key = transaction_ids.provider_id.test_secret_key
                        url = 'https://restapidev.payplus.co.il/api/v1.0/'
                        _logger.info("Using TEST PayPlus API")

                    elif transaction_ids.provider_id.state == 'enabled':
                        api_key = transaction_ids.provider_id.production_api_key
                        secret_key = transaction_ids.provider_id.production_secret_key
                        url = 'https://restapi.payplus.co.il/api/v1.0/'
                        _logger.info("Using PRODUCTION PayPlus API")

                    else:
                        _logger.warning("Unknown provider state: %s", transaction_ids.provider_id.state)
                        raise ValidationError("Invalid provider state for PayPlus.")

                    if not api_key or not secret_key:
                        _logger.error("Missing API credentials for provider %s", transaction_ids.provider_id.name)
                        raise ValueError("PayPlus credentials are not set. Please check the payment provider configuration.")

                    headers = {
                        "accept": "application/json",
                        "api-key": api_key,
                        "secret-key": secret_key,
                        "content-type": "application/json"
                    }
                    payload = {
                        "transaction_uid": transaction_uid,
                        "amount": self.amount_total,
                    }
                    _logger.info("Sending approval request with payload: %s", payload)

                    response = requests.post(f"{url}Transactions/ChargeByTransactionUID", json=payload, headers=headers)
                    _logger.info("HTTP status: %s", response.status_code)

                    try:
                        response.raise_for_status()
                    except Exception as e:
                        _logger.exception("Error during PayPlus approval API call")
                        raise

                    result = response.json()
                    _logger.info("PayPlus Transactions Approval response: %s", result)

                    status = result.get('results', {}).get('status')
                    description = result.get('results', {}).get('description')
                    if status != 'success':
                        _logger.error("Approval failed: %s", description)
                        raise ValidationError(f"PayPlus Transactions Approval failed: {description}")

                    approval_transaction_uid = result.get('data', {}).get('transaction', {}).get('uid')
                    _logger.info("New approval transaction UID: %s", approval_transaction_uid)
                    self.message_post(body=f'Payplus J5 Transaction Approved Manully- {approval_transaction_uid}')
                    self.transaction_number = approval_transaction_uid
                    self.is_j5_order_paid = True
                    self.is_warning_div = False


                    if not approval_transaction_uid:
                        raise ValidationError("PayPlus Approval Transaction UID missing in response")

                    # self.is_warning_div = False
                    _logger.info("SO %s marked as PAID", self.name)



    def action_confirm(self):
        res = super(SaleOrderInherit,self).action_confirm()
        for res in self:
            if res.payplus_payment_status not in ['in_payment','paid']:
                res.payplus_payment_status = 'not_paid'
        return res

    @api.depends('invoice_ids.payment_state')
    def _compute_payplus_payment_status(self):
        _logger.info("--------_compute_payplus_payment_status-------------- %s",self)
        for order in self:
            if order.invoice_ids:
                if any(inv.payment_state == 'paid' for inv in order.invoice_ids):
                    order.payplus_payment_status = 'paid'
                elif any(inv.payment_state in ('in_payment', 'partial') for inv in order.invoice_ids):
                    order.payplus_payment_status = 'paid'
                else:
                    order.payplus_payment_status = 'not_paid'

    def _compute_transaction_count(self):
        for order in self:
            order.transaction_count = self.env['payment.transaction'].search_count([('sale_order_ids', 'in', order.id)])

    def action_show_transactions(self):
        self.ensure_one()
        return {
            'name': 'Payment Transactions',
            'type': 'ir.actions.act_window',
            'res_model': 'payment.transaction',
            'view_mode': 'list,form',
            'domain': [('sale_order_ids', 'in', self.id)],
            'context': {'default_sale_order_ids': [self.id]},
            'target': 'current',
        }

    # @api.depends('transaction_ids', 'invoice_ids.payment_state')
    # def _compute_is_warning_div(self):
    #     for order in self:
    #         show_warning = False
    #         transaction = order.transaction_ids and order.transaction_ids[0] or None
    #         if not order.transaction_number and transaction and transaction.provider_id.code == 'payplus' and transaction.payplus_payment_success_response_json:
                
    #             try:
    #                 payplus_response = transaction.payplus_payment_success_response_json
    #                 json_response = (
    #                     json.loads(payplus_response)
    #                     if isinstance(payplus_response, str)
    #                     else payplus_response
    #                 )
    #                 payment_type = json_response.get('type')
    #                 if payment_type == 'Approval':
    #                     show_warning = True
    #             except Exception as e:
    #                 _logger.warning("Failed to parse PayPlus JSON response: %s", e)

    #         # # Step 1: Get the PayPlus transaction
    #         # transaction = order.transaction_ids and order.transaction_ids[0] or None
    #         # if (
    #         #     transaction and
    #         #     transaction.provider_id.code == 'payplus' and
    #         #     transaction.payplus_payment_success_response_json
    #         # ):
    #         #     try:
    #         #         payplus_response = transaction.payplus_payment_success_response_json
    #         #         json_response = (
    #         #             json.loads(payplus_response)
    #         #             if isinstance(payplus_response, str)
    #         #             else payplus_response
    #         #         )
    #         #         payment_type = json_response.get('type')
    #         #         _logger.info("PayPlus payment_type: %s", payment_type)

    #         #         # Step 2: Check if payment_type is 'Approval'
    #         #         if payment_type == 'Approval':
    #         #             # Step 3: Then check invoice is unpaid
    #         #             if order.invoice_ids:
    #         #                 payment_states = order.invoice_ids.mapped('payment_state')
    #         #                 if any(state not in ['paid', 'partial', 'reversed', 'in_payment'] for state in payment_states):
    #         #                     show_warning = True
    #         #             else:
    #         #                 show_warning = True

    #         #     except Exception as e:
    #         #         _logger.warning("Failed to parse PayPlus JSON response: %s", e)

    #         order.is_warning_div = show_warning

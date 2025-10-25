from odoo import models, fields, api
import json
import requests
from odoo.exceptions import UserError
from datetime import date
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    payplus_transaction_id = fields.Char(string="PayPlus Transaction ID", help="The unique identifier for the transaction.")
    payment_provider_id = fields.Many2one(
        'payment.provider',
        string="Payment Provider",
        help="The payment provider used for this transaction."
    )
    is_refund_button = fields.Boolean(string="Refund Button Show Or Not", compute="_check_is_refund_button")

    def _check_is_refund_button(self):
        for res in self:
            if res.payplus_transaction_id and res.payment_state != 'reversed':
                transaction_id = res.transaction_ids[0] if res.transaction_ids else None
                if transaction_id and transaction_id.provider_id.code == 'payplus' and transaction_id.payplus_payment_success_response_json:
                    payplus_response = transaction_id.payplus_payment_success_response_json
                    json_response = json.loads(payplus_response) if isinstance(payplus_response, str) else payplus_response
                    payment_type = json_response.get('type')
                    _logger.info("payment_type for refund button %s", payment_type)
                    if payment_type == 'Approval':
                        res.is_refund_button = False
                    else:
                        res.is_refund_button = True
                else:
                    res.is_refund_button = True
            else:
                res.is_refund_button = False

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        _logger.info("Creating account move with vals: %s", res)
        transaction_id = res.transaction_ids[0] if res.transaction_ids else None
        _logger.info("Transaction IDs: %s", transaction_id)
        if transaction_id and transaction_id.provider_id.code == 'payplus' and transaction_id.payplus_payment_success_response_json:
            payplus_response = transaction_id.payplus_payment_success_response_json
            json_response = json.loads(payplus_response) if isinstance(payplus_response, str) else payplus_response
            res.payplus_transaction_id = json_response.get('transaction_uid')
            res.payment_provider_id = self.env['payment.provider'].search([('code', '=', 'payplus')], limit=1)
        return res

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.move_type == 'out_invoice' and self.line_ids.sale_line_ids.order_id:
            payplus_response = self.transaction_ids[0].payplus_payment_success_response_json if self.transaction_ids else False
            json_response = json.loads(payplus_response) if isinstance(payplus_response, str) else payplus_response
            if json_response and json_response['type'] == 'Approval':
                _logger.info("Sale PayPlus Response: %s", json_response)


                if self.payment_provider_id.state == 'test':
                    api_key = self.payment_provider_id.test_api_key
                    secret_key = self.payment_provider_id.test_secret_key
                    url = 'https://restapidev.payplus.co.il/api/v1.0/'

                elif self.payment_provider_id.state == 'enabled':
                    api_key = self.payment_provider_id.production_api_key
                    secret_key = self.payment_provider_id.production_secret_key
                    url = 'https://restapi.payplus.co.il/api/v1.0/'
                    # url = 'https://restapidev.payplus.co.il/api/v1.0/'

                # url = 'https://restapidev.payplus.co.il/api/v1.0/'
                # api_key = '2b47ad68-973f-49f7-8f02-51a870fa1671'
                # secret_key = '0e4b850f-3319-4c6b-8fe0-d380ae72ae6a'
                if not api_key or not secret_key:
                    raise ValueError("PayPlus credentials are not set. Please check the payment provider configuration.")
                headers = {
                    "accept": "application/json",
                    "api-key": api_key,
                    "secret-key": secret_key,
                    "content-type": "application/json"
                }

                payload = {
                    "transaction_uid": json_response['transaction_uid'],
                    "amount":self.amount_total,
                }
                response = requests.post(f"{url}Transactions/ChargeByTransactionUID", json=payload, headers=headers)
                response.raise_for_status() 
                result = response.json()
                _logger.info("PayPlus Transactions Approval response: %s", result)
                if not result['results']['status'] == 'success':
                    raise ValidationError(f"PayPlus Transactions Approval failed: {result['results']['description']}")

                approval_transaction_uid = result['data']['transaction']['uid']
                _logger.info("### gettting new transaction uid from approval %s",approval_transaction_uid)
                if not approval_transaction_uid:
                    raise ValidationError(f"PayPlus Transactions Uid Not Getting Something Wrong : {result['data']['transaction']}")
                
                self.payplus_transaction_id = approval_transaction_uid

                if self.payment_provider_id.journal_id:
                    journal_id = self.payment_provider_id.journal_id.id
                else:
                    journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id

                payment_transaction_id = self.transaction_ids[0]
                payment = self.env['account.payment'].create({
                    'partner_id': payment_transaction_id.partner_id.id,
                    'memo': payment_transaction_id.reference,
                    'amount': payment_transaction_id.amount,
                    'journal_id': journal_id,
                    'company_id' : payment_transaction_id.company_id.id

                })

                self.payment_ids = [(4, payment.id)]
                payment.action_post()
                if payment:
                    status = payment.state
                    _logger.info("### payment status %s", status)
                    if status == 'in_process':
                        self.payment_state = 'in_payment'
                    if status == 'paid':
                        self.payment_state = 'paid'

                # self.is_post_processed = True
                payment_move_line = payment.move_id.line_ids.filtered(
                            lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                        )
                invoice_move_line = self.line_ids.filtered(
                    lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                )
                if payment_move_line and invoice_move_line:
                    (payment_move_line + invoice_move_line).reconcile()
    
        return res

    def action_refund_payplus(self):
        for res in self:
            if res.state != 'posted' and res.move_type != 'out_invoice':
                raise UserError("Only posted invoices can be refunded.")
            if not res.payplus_transaction_id:
                raise UserError("No transaction found for this invoice.")
            if not res.transaction_ids:
                raise UserError("No transaction IDs found for this invoice.")

            # payment_provider = res.transaction_ids.provider_id
            transaction_uid = res.payplus_transaction_id
            amount = res.amount_total

            if self.payment_provider_id.state == 'test':
                    api_key = self.payment_provider_id.test_api_key
                    secret_key = self.payment_provider_id.test_secret_key
                    url = 'https://restapidev.payplus.co.il/api/v1.0/'

            elif self.payment_provider_id.state == 'enabled':
                    api_key = self.payment_provider_id.production_api_key
                    secret_key = self.payment_provider_id.production_secret_key
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
            _logger.info("Refund response: %s", result)
            if result and result['results']['status'] == 'success':
                refund_transaction_id = result['data']['transaction']['uid']
                reverse = res._reverse_moves()
                if reverse:
                    reverse.payplus_transaction_id = refund_transaction_id
                    reverse.action_post()
                    payment = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=reverse.id).create({
                                'payment_date' : date.today(),
                                # 'journal_id' : reverse.journal_id.id
                    })
                    if payment:
                        payment.sudo()._create_payments()
                        res.payment_state = 'reversed'
            else:
                raise UserError(f"Refund failed Something went wrong : {result}")
                

                


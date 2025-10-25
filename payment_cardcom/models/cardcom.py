import requests
from odoo import api, fields, models
# from odoo.addons.payment.models.payment_acquirer import ValidationError
import logging
_logger = logging.getLogger(__name__)
import json
from odoo.exceptions import ValidationError
from urllib.parse import parse_qs, urlparse


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    transaction_number = fields.Char(string="Transaction Number")
    is_warning_div = fields.Boolean(string="Warning Div",default=False)
    transaction_count = fields.Integer(string="Transaction Count", compute="_compute_transaction_count")
    is_j5_order_paid = fields.Boolean(string="Flag For J5 Order Paid",default=False)

    def _compute_transaction_count(self):
        for order in self:
            order.transaction_count = self.env['payment.transaction'].search_count([('sale_order_ids', 'in', order.id)])

    def approve_j5_order(self):
        transaction_ids = self.transaction_ids and self.transaction_ids[0] or None
        _logger.info("Found %s transactions for SO %s", len(transaction_ids), self.name)
        if transaction_ids:
            provider = transaction_ids.provider_id
            username = provider.cardcom_api_name
            password = provider.cardcom_api_password  # or however it's stored
            terminal = provider.cardcom_terminal_number
            suspended_deal_id = self.transaction_number  # or wherever you store it

            if not all([username, password, terminal, suspended_deal_id]):
                raise ValidationError("Missing required data for Suspended Deal activation")

            base_url = "https://secure.cardcom.solutions/Interface/SuspendedDealActivate.aspx"
            params = {
            "username": username,
            "userpassword": password,
            "terminalnumber": terminal,
            "SuspendedDealId": suspended_deal_id,
            }

            _logger.info("Activating suspended deal with params: %s", params)

            try:
                response = requests.get(base_url, params=params)
                _logger.info("HTTP status: %s", response.status_code)
                response.raise_for_status()  # Raise error if not 2xx

                result_text = response.text
                _logger.info("Response content: %s", result_text)
                parsed_data = parse_qs(result_text)
                _logger.info("J5 Response -> response_dict %s",parsed_data)
                internal_deal_number = parsed_data.get('InternalDealNumber', [None])[0]
                self.transaction_number = internal_deal_number
                self.is_j5_order_paid = True
                transaction_ids.cardcom_j5_response_json = result_text

                # if not self.invoice_ids:
                #     invoice = self._create_invoices()
                #     invoice.transaction_id = internal_deal_number
                #     invoice.action_post()
                #     if provider.journal_id:
                #             journal_id = provider.journal_id.id
                #     else:
                #         journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id

                #     payment = self.env['account.payment'].create({
                #         'partner_id': invoice.partner_id.id,
                #         'ref': self.name,
                #         'amount': invoice.amount_total,
                #         'journal_id': journal_id,
                #     })

                #     invoice.payment_id = payment.id
                #     print("payment created")
                #     payment.action_post()
                #     # invoice.is_post_processed = True
                #     print("action payment posted")
                #     payment_move_line = payment.move_id.line_ids.filtered(
                #                 lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                #             )
                #     invoice_move_line = invoice.line_ids.filtered(
                #         lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                #     )
                #     # Perform reconciliation
                #     if payment_move_line and invoice_move_line:
                #         (payment_move_line + invoice_move_line).reconcile()

                # Optionally, parse the response if it's in XML/JSON format
                # For simplicity, assuming success if status code is 200
                self.message_post(body=f'CardCom J5 Transaction Approved Manully- {internal_deal_number}')
                self.is_j5_order_paid = True
                self.is_warning_div = False
                # self.transaction_number = suspended_deal_id
                _logger.info("Order %s marked as paid via suspended deal", self.name)

            except requests.RequestException as e:
                _logger.exception("Error activating suspended deal")
                raise ValidationError(f"Failed to activate suspended deal: {str(e)}")


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


class PaymentProviderCardcom(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('cardcom', 'Cardcom')],ondelete={'cardcom': 'set default'})
    cardcom_terminal_number = fields.Char('Terminal Number', required_if_provider='cardcom')
    cardcom_api_name = fields.Char('API Name', required_if_provider='cardcom')
    cardcom_api_password = fields.Char('API Password', required_if_provider='cardcom')
    success_redirect_url = fields.Char("Success Redirect Url")
    failed_redirect_url = fields.Char("Failed Redirect URL")
    webhook_url = fields.Char("Webhook URL")
    cardcom_charge_method = fields.Selection(
        [('1','Charge'),('2','Approval')],
        string="Cardcom Charge Method",
        default='2',
        required=True
    )
    with_invoice = fields.Boolean(string="With Invoice ?", default=False)

    def _get_cardcom_urls(self):
        """Get Cardcom Low Profile endpoint URLs."""
        return {
            'production': 'https://secure.cardcom.solutions/LowProfile/',
            'test': 'https://secure.cardcom.solutions/LowProfile/'
        }

    def cardcom_form_generate_values(self, values):
        """Generate values for the form redirect to Cardcom."""
        values.update({
            'terminalNumber': self.cardcom_terminal_number,
            'api_key': self.cardcom_api_key,
            'sum': int(values['amount'] * 100),  # Cardcom expects amounts in cents
            'currency': values['currency'].name,
            'myOrder': values['reference'],
            'goodUrl': '/payment/cardcom/return',
            'errorUrl': '/payment/cardcom/cancel',
        })
        return values

    def cardcom_get_form_action_url(self):
        """Return the form action URL for Cardcom."""
        return self._get_cardcom_urls().get(self.state, 'test')

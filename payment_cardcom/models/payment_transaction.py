# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from werkzeug.utils import redirect

from werkzeug.urls import url_encode, url_join

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_stripe import const
from odoo.addons.payment_stripe.controllers.main import StripeController


_logger = logging.getLogger(__name__)
from odoo import http

from odoo import http
from odoo.http import request
import requests

class CardcomPaymentController(http.Controller):

    @http.route('/cardcom/payment/process/document', type='http', auth='public', methods=['GET','POST'], csrf=False)
    def process_document_response(self, **data):
        print("process_document_response")
        _logger.info("---- process_document_response --------")
        # data = request.httprequest.get_json()
        print(data)
        _logger.info("---- data --------")

        inv_sudo = request.env['account.move'].sudo().search([('id','>',0)],order='id desc',limit=1)
        inv_sudo.write({
            'cardcom_doc_response_json':data
        })

    @http.route('/cardcom/payment/process/response', type='http', auth='public', methods=['GET','POST'], csrf=False)
    def process_payment_response(self, **data):
        print("process_payment_response")
        _logger.info("------------------ cardcom/payment/process/response %s",data)
        # data = request.httprequest.get_json()
        # print(data)
        # print(data['lowprofilecode'])
        tx_sudo = request.env['payment.transaction'].sudo().search([('cardcom_profile_id','=',data['lowprofilecode'])])
        tx_sudo.write({
            'cardcom_response_json':data
        })
        if data['ResponseCode'] == '0':
            if tx_sudo.state != 'done':
                tx_sudo.state = 'done'
            return request.redirect('/cardcom/payment/success')
        else:
            return request.redirect('/cardcom/payment/failure')

    @http.route('/cardcom/payment/webhook', type='http', auth='public', methods=['GET','POST'], csrf=False)
    def process_payment_webhook(self, **post):
        print("process_payment_webhook")
        _logger.info(" ----- process_payment_webhook ------ ")
        
        data = request.httprequest.get_json()
        _logger.info("cardcom/payment/webhook DAta ########### %s",data)
        print(data)
        print(data['LowProfileId'])
        tx_sudo = request.env['payment.transaction'].sudo().search([('cardcom_profile_id','=',data['LowProfileId'])],limit=1)
        tx_sudo.write({
            'cardcom_response_json':data
        })
        # if data['ResponseCode'] == 0:
        #     tx_sudo.state = 'done'
        #     # Redirect the user to the status page.
        #     return request.redirect('/cardcom/payment/success')
        # else:
        #     return request.redirect('/cardcom/payment/failure')
# {'ResponseCode': 0, 'Description': 'העסקה בוצעה בהצלחה', 'TerminalNumber': 1000, 'LowProfileId': '73c183bf-0146-4cdd-8e02-08007fa37a07', 'TranzactionId': 193884095, 'ReturnValue': 'Z12332Xaa', 'Operation': 'ChargeOnly', 'UIValues': {'CardOwnerEmail': 'testsite@test.co.il', 'CardOwnerName': 'Card Owner', 'CardOwnerPhone': '039436100', 'CardOwnerIdentityNumber': '040617649', 'NumOfPayments': 1, 'CardYear': 2025, 'CardMonth': 11, 'CustomFields': [], 'IsAbroadCard': False}, 'DocumentInfo': {'ResponseCode': 0, 'Description': 'העסקה בוצעה בהצלחה', 'DocumentType': 'Receipt', 'DocumentNumber': 571393, 'AccountId': 0, 'ForeignAccountNumber': None, 'SiteUniqueId': None, 'DocumentUrl': 'https://secure.cardcom.solutions/api/v11/documents/DownloadDoc/?c=1&code=4XZ2Z7QGGeY+c8caYr4Q+0GpI+pkPytX/Gd7YaTtoXzkTVO/GjLEUQpXJKDYrbq3'}, 'TokenInfo': None, 'SuspendedInfo': None, 'TranzactionInfo': {'ResponseCode': 0, 'Description': 'העסקה בוצעה בהצלחה', 'TranzactionId': 193884095, 'TerminalNumber': 1000, 'Amount': 123.67, 'CoinId': 1, 'CouponNumber': '38001032', 'CreateDate': '2024-12-03T09:20:18', 'Last4CardDigits': 0, 'Last4CardDigitsString': '0000', 'FirstCardDigits': 458000, 'JParameter': '0', 'CardMonth': 11, 'CardYear': 25, 'ApprovalNumber': '12345', 'FirstPaymentAmount': 0.0, 'ConstPaymentAmount': 0.0, 'NumberOfPayments': 1, 'CardInfo': 'Israeli', 'CardOwnerName': 'Card Owner', 'CardOwnerPhone': '039436100', 'CardOwnerEmail': 'testsite@test.co.il', 'CardOwnerIdentityNumber': '040617649', 'Token': '4cf8e168-261e-4613-8d20-000332986b24', 'CardName': 'ויזה רגיל', 'SapakMutav': '', 'Uid': '21121517002429612920744', 'ConcentrationNumber': None, 'DocumentNumber': 571393, 'DocumentType': 'Receipt', 'Rrn': '', 'Brand': 'Visa', 'Acquire': 'Laumicard', 'Issuer': 'CAL', 'PaymentType': 'Standard', 'CardNumberEntryMode': 'Phone', 'DealType': 'Debit', 'IsRefund': False, 'DocumentUrl': None, 'CustomFields': [], 'IsAbroadCard': False}, 'ExternalPaymentVector': 'NoneOrUnknown', 'Country': 'PK', 'UTM': None}

    @http.route('/cardcom/payment/trn/webhook', type='http', auth='public', methods=['GET','POST'], csrf=False)
    def process_payment_trn_webhook(self, **post):
        print("process_payment_trn_webhook")
        data = request.httprequest.get_json()
        _logger.info("Main cardcom/payment/trn/webhook DAta ########### %s",data)
        print(data)
        print(data['LowProfileId'])
        tx_sudo = request.env['payment.transaction'].sudo().search([('cardcom_profile_id','=',data['LowProfileId'])])
        tx_sudo.write({
            'cardcom_wh_response_json':data
        })
        request.env.cr.commit()
        tx_sudo._set_done()
        pos_order = tx_sudo.pos_order_id
        _logger.info("--------- pos_order -------- %s",pos_order)
        if pos_order:
            if pos_order and pos_order.state == 'draft':
                _logger.info("Processing POS order %s after Cardcom payment", pos_order.name)

                # Add payment line if not already added
                payment_method = request.env['pos.payment.method'].sudo().browse(4)
                account_payment = request.env['account.payment'].sudo().create({
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'partner_id': pos_order.partner_id.id if pos_order.partner_id else False,
                    'amount': tx_sudo.amount,
                    'journal_id': payment_method.journal_id.id  or payment_method.online_payment_provider_ids.journal_id.id,  # must be set in POS Payment Method
                    'ref': tx_sudo.reference,
                })

                # Now create the POS payment and link
                pos_order.add_payment({
                    'pos_order_id': pos_order.id,
                    'amount': tx_sudo.amount,
                    'name': tx_sudo.reference,
                    'payment_method_id': payment_method.id,
                    'online_account_payment_id': account_payment.id,
                })


                # Mark order paid and process
                if pos_order._is_pos_order_paid():
                    pos_order._process_saved_order(False)
                    pos_order._send_order()
                    pos_order.write({'state': 'paid'})

            request.env.cr.commit()
            # return {"result": "success"}
        else:
            tx_sudo.action_process_transaction(data)
            # return {"result":"success"}
        

    @http.route('/cardcom/payment/success', type='http', auth='public', website=True, csrf=False)
    def cardcom_payment_success(self, **post):
        print("cardcom_payment_success")
        _logger.info("--- cardcom_payment_success ----")
        return request.render("payment_cardcom.cardcom_success")  # URL to redirect to after processing

    @http.route('/cardcom/payment/failure', type='http', auth='public', website=True, csrf=False)
    def cardcom_payment_failue(self, **post):
        print("cardcom_payment_failue")
        _logger.info("--- cardcom_payment_failue ----")
        return request.render("payment_cardcom.cardcom_failure")  # URL to redirect to after processing

    @http.route('/cardcom/payment/process', type='http', auth='public', website=True, csrf=False)
    def process_payment(self, **post):
        # Handle form data (e.g., form fields from the template)
        # Example: process the payment data in `post` dictionary
        redirect_url = post.get('redirect_url')
        _logger.info("########## **post ############ %s",post)
        _logger.info("########## redirect_url ############ %s",redirect_url)
        # After processing, redirect to a success page or another URL
        print("redirect_url payment process")
        print(redirect_url)
        data = {
            "iframe_url": redirect_url
        }
        return redirect(redirect_url)

        # return request.render("payment_cardcom.cardcom_iframe_form",data)  # URL to redirect to after processing

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    cardcom_profile_id = fields.Char("Profile ID")
    return_value = fields.Char("Return Value")
    cardcom_response_json = fields.Text("Cardcom Response Json")
    cardcom_wh_response_json = fields.Text("Cardcom Webhook Response Json")
    cardcom_j5_response_json = fields.Text("Cardcom J5 Response Json")


    def action_process_transaction(self,json_response=False):
        print("action_process_transaction")
        self.sale_order_ids.action_confirm()
        _logger.info("--- action_process_transaction --- %s",json_response)
        type = json_response.get('Operation')
        if type == 'SuspendedDeal':
            self.sale_order_ids.transaction_number = json_response.get('SuspendedInfo').get('SuspendedDealId')
            self.sale_order_ids.is_warning_div = True
            self.sale_order_ids.message_post(body=f'CardCom Transaction Number. - {json_response.get("SuspendedInfo").get("SuspendedDealId")}')
        if not type == 'SuspendedDeal':
            self.sale_order_ids.message_post(body=f'CardCom Transaction Number. - {json_response.get("TranzactionId")}')
            self.sale_order_ids.transaction_number = json_response.get('TranzactionId')
            invoice = self.sale_order_ids._create_invoices()
            if json_response:
                transaction_id = json_response.get('TranzactionId')
                invoice.transaction_id = transaction_id

                # document_url = json_response.get('DocumentInfo', {}).get('DocumentUrl')
                doc_info = json_response.get('DocumentInfo') or {}
                DocumentNumber = doc_info.get('DocumentNumber')
                DocumentUrl = doc_info.get('DocumentUrl')
                invoice.document_num = DocumentNumber
                invoice.document_url = DocumentUrl

                invoice.is_refund_button = True

            invoice.action_post()

            if self.provider_id.journal_id:
                    journal_id = self.provider_id.journal_id.id
            else:
                journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id
            payment = self.env['account.payment'].create({
                'partner_id': self.partner_id.id,
                'ref': self.reference,
                'amount': self.amount,
                'journal_id': journal_id,
            })
            _logger.info("###### payment ###### create from action_process_transaction")

            self.payment_id = payment.id
            print("payment created")
            payment.action_post()
            self.is_post_processed = True
            print("action payment posted")
            payment_move_line = payment.move_id.line_ids.filtered(
                        lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
                    )
            invoice_move_line = invoice.line_ids.filtered(
                lambda line: line.account_id.reconcile and line.account_id.account_type == 'asset_receivable' and line.amount_residual != 0
            )
            # Perform reconciliation
            if payment_move_line and invoice_move_line:
                (payment_move_line + invoice_move_line).reconcile()

    def action_test(self):
        txn = self
        txn._set_done()
        txn._reconcile_after_done()

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'cardcom':
            return res
        return processing_values


    def _get_specific_processing_values(self, processing_values):
        print("for _get_specific_processing_values")
        """ Override of payment to return Stripe-specific processing values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_processing_values(processing_values)
        # if self.provider_code != 'cardcom' or self.operation == 'online_token':
        if self.provider_code != 'cardcom':
            return res
        _logger.info("--- _get_specific_processing_values --- %s",processing_values)
        # print('processing_values')
        # print(processing_values)
        # print('res')
        # print(res)

        # call cardcom api

        method = self.provider_id.cardcom_charge_method 
        # print("---- method -------",method)
        operation = 'ChargeOnly' if method == '1' else 'SuspendedDeal'
        products = []
        name = processing_values['reference']
        _logger.info("--------------------> Name --->> %s",name)
        is_pos_order = False
        if name.startswith('Order'):
            base_ref = '-'.join(name.split('-')[:-1])
            order = self.env['pos.order'].sudo().search([('pos_reference','=',base_ref)])
            is_pos_order = True
            operation = 'ChargeOnly'
            _logger.info("---------------> order getting %s",order)
            lines = order.lines
            for line in lines:
                products.append({
                    "Quantity" : line.qty,
                    "Description": line.product_id.display_name,
                    "UnitCost": line.price_subtotal_incl / line.qty   
                })
        else:
            order = self.env['sale.order'].sudo().search([('name','=',name.split('-'))])
            lines = order.order_line
            for line in lines:
                products.append({
                    "Quantity" : line.product_uom_qty,
                    "Description": line.product_id.display_name,
                    "UnitCost": line.price_total / line.product_uom_qty   
                })


        payment_data = {
          "Operation" : operation,
          "TerminalNumber": self.provider_id.cardcom_terminal_number,
          "ApiName": self.provider_id.cardcom_api_name,
          "ReturnValue": "Z12332Xaa",
          "Amount":processing_values['amount'],
          "SuccessRedirectUrl": self.provider_id.success_redirect_url,
          "FailedRedirectUrl": self.provider_id.failed_redirect_url,
          "WebHookUrl": self.provider_id.webhook_url,
          "Document": {
            "Name" : order.partner_id.name or "admin",
            "To": order.partner_id.display_name or "admin",
            "Email": order.partner_id.email or "testing@mail.com",
            "Products": products
          },
        #   "AdvancedDefinition": {
        #     "VirtualTerminal": {
        #         "IsEnable": True
        #         }
        #     },
        }

        # if self.provider_id.with_invoice:
        #     payment_data["Document"] = {
        #         "Name" : sale_order.partner_id.name,
        #         "To": sale_order.partner_id.display_name,
        #         "Email": sale_order.partner_id.email,
        #         "Products": products
        #     }

        _logger.info("--- payment_data ---- %s",payment_data)
        # print("--- payment_data --- ",payment_data)
        response = requests.post("https://secure.cardcom.solutions/api/v11/LowProfile/Create", json=payment_data, headers={})
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        result = response.json()  # Parse the JSON response if needed
        # print("result")
        # print(result)
        _logger.info("--- result --- %s",result)
        redirect_url = result['Url']
        self.sudo().cardcom_profile_id = result['LowProfileId']
        if is_pos_order:
            self.sudo().pos_order_id = order.id
        return {
            "redirect_url": redirect_url
        }

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
from odoo.http import request
import requests

class CardcomPosPaymentController(http.Controller):

    @http.route('/cardcom/pos/payment/process', type='http', auth='public', website=True, csrf=False)
    def cardcom_pos_process_payment(self, **post):
        _logger.info("/cardcom/pos/payment/process Data %s",post)
        redirect_url = post.get('redirect_url')
        if not redirect_url:
            _logger.error("Redirect URL is missing in the request.")
        return redirect(redirect_url)

    @http.route('/cardcom/pos/payment/success', type='http', auth='public', methods=['GET','POST'], csrf=False)
    def cardcom_pos_payment_success(self, **data):
        _logger.info("------------------ cardcom/pos/payment/success %s",data)
        tx_sudo = request.env['payment.transaction'].sudo().search([('cardcom_pos_profile_id','=',data['lowprofilecode'])])
        _logger.info("------------------ tx_sudo cardcom/pos/payment/success %s",tx_sudo)
        tx_sudo._set_done()
        tx_sudo._handle_notification_data('cardcom_pos', data)
        return request.redirect('/payment/status')

    @http.route('/cardcom/pos/payment/trn/webhook', type='http', auth='public', methods=['GET','POST'], csrf=False)
    def process_pos_payment_trn_webhook(self, **post):
        data = request.httprequest.get_json()
        _logger.info("Main cardcom/pos/payment/trn/webhook data ########### %s",data)
        tx_sudo = request.env['payment.transaction'].sudo().search([('cardcom_pos_profile_id','=',data['LowProfileId'])])
        tx_sudo.write({
            'cardcom_pos_wh_response_json':data
        })
        
    @http.route('/cardcom/pos/payment/failure', type='http', auth='public', website=True, csrf=False)
    def cardcom_pos_payment_failue(self, **post):
        _logger.info("--- cardcom_payment_failue ----")
        return request.render("payment_cardcom_pos.cardcom_pos_failure")  

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    cardcom_pos_profile_id = fields.Char("Profile ID")
    cardcom_pos_response_json = fields.Text("Cardcom Response Json")
    cardcom_pos_wh_response_json = fields.Text("Cardcom Webhook Response Json")

    def _get_tx_from_notification_data(self, provider_code, data):
        tx = super()._get_tx_from_notification_data(provider_code, data)
        if provider_code != 'cardcom_pos' or tx:
            return tx
        LowProfileId = data.get('LowProfileId')
        if not LowProfileId:
            raise ValidationError("cardcom_pos: Missing page_request_uid in response")

        tx = self.search([('cardcom_pos_profile_id', '=', LowProfileId), ('provider_code', '=', 'cardcom_pos')])
        if not tx:
            raise ValidationError(f"cardcom_pos : No transaction found matching UID {LowProfileId}")
        return tx

    def _process_notification_data(self, data):
        super()._process_notification_data(data)
        if self.provider_code != 'cardcom_pos':
            return
        _logger.info("########## _process_notification_data ############ %s", data)
        status = data.get('status')
        payment_type = data.get('method') or data.get('brand_name') or ''
        payment_type = payment_type.lower()
        _logger.info("########## payment_type ############ %s", payment_type)
        payment_method = self.env['payment.method'].search([('code', '=', 'cardcom_pos'),('active','=',True)], limit=1)
        _logger.info("########## payment_method ############ %s , %s", payment_method , payment_method.name)
        if payment_method:
            self.payment_method_id = payment_method
        if status == '0':
            self._set_done()
        else:
            self._set_canceled()

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'cardcom_pos':
            return res
        return processing_values

    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'cardcom_pos':
            return res
        _logger.info("--- _get_specific_processing_values --- %s",processing_values)

        products = []
        name = processing_values['reference']
        _logger.info("--- name ---- %s",name)
        if name.startswith('Order'):

            # old_trans = self.sudo().search([('reference','=',name)])
            # _logger.info("old_trans ------------- %s",old_trans)
            # if old_trans.exists():
            pos_ref_name = '-'.join(name.split('-')[:-1])
            _logger.info("--- name ---- %s",pos_ref_name)
            
            order = self.env['pos.order'].sudo().search([('pos_reference','=',name)])
            if not order:
                order = self.env['pos.order'].sudo().search([('pos_reference','=',pos_ref_name)])
            _logger.info("--- POS order ---- %s",order)

            operation = 'ChargeOnly'
            lines = order.lines
            for line in lines:
                products.append({
                    "Quantity" : line.qty,
                    "Description": line.product_id.display_name,
                    "UnitCost": line.price_subtotal_incl / line.qty   
                })

        _logger.info("-- products --- %s",products)
        base_url = self.provider_id.get_base_url()
        success_redirect_url = 'cardcom/pos/payment/success'
        failed_redirect_url = 'cardcom/pos/payment/failure'
        payment_data = {
          "Operation" : operation,
          "TerminalNumber": self.provider_id.cardcom_pos_cardcom_terminal_number,
          "ApiName": self.provider_id.cardcom_pos_cardcom_api_name,
          "ReturnValue": "Z12332Xaa",
          "Amount":processing_values['amount'],
          "SuccessRedirectUrl": base_url+success_redirect_url,
          "FailedRedirectUrl": base_url+failed_redirect_url,
          "WebHookUrl": self.provider_id.cardcom_pos_webhook_url,
          "Document": {
            "Name" : order.partner_id.name or "admin",
            "To": order.partner_id.display_name or "admin",
            "Email": order.partner_id.email or "testing@mail.com",
            "Products": products
          },
          "AdvancedDefinition": {
                "VirtualTerminal": {
                "IsEnable": True
                }
          },
          
        }

        _logger.info("--- payment_data ---- %s",payment_data)
        response = requests.post("https://secure.cardcom.solutions/api/v11/LowProfile/Create", json=payment_data, headers={})
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        result = response.json()  # Parse the JSON response if needed
        _logger.info("--- result --- %s",result)
        redirect_url = result['Url']
        response_code = result.get('ResponseCode')
        if response_code == 0:
            self.sudo().cardcom_pos_profile_id = result['LowProfileId']
            # self.sudo().pos_order_id = order.id
            return {
                "redirect_url": redirect_url
            }
        else:
            raise ValueError(_("Failed to generate CardCom payment page link."))

# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
_logger = logging.getLogger(__name__)
from werkzeug.utils import redirect
import json
from odoo import _, fields, models,http
from odoo.addons.payment import utils as payment_utils
from odoo.http import request
import requests
from odoo.exceptions import ValidationError
from odoo.addons.payment_payplus import const

class PayPlusPaymentController(http.Controller):
    
    @http.route('/payplus/payment/process', type='http', auth='public', website=True, csrf=False)
    def process_payment(self, **post):
        _logger.info("/payplus/payment/process Data %s",post)
        redirect_url = post.get('redirect_url')
        if not redirect_url:
            _logger.error("Redirect URL is missing in the request.")
            return request.render("payment_payplus.payplus_failure", {"error": "Redirect URL is missing."})
        data = {
            "iframe_url": redirect_url
        }
        return request.render("payment_payplus.payplus_iframe_form",data) 

    @http.route('/payplus/payment/success', type='http', auth='public', website=True, csrf=False)
    def payplus_payment_success(self, **post):
        page_req_uid = post.get('page_request_uid')
        _logger.info("payplus_payment_success Data %s", post)
        tx = request.env['payment.transaction'].sudo().search([
        ('payplus_page_req_uid', '=', page_req_uid),
        ('provider_code', '=', 'payplus')
        ], limit=1)
        tx.payplus_payment_success_response_json = json.dumps(post)
        transaction_uid = post.get('transaction_uid')
        sale_ids = tx.sale_order_ids
        pos_id = tx.pos_order_id
        # sale_ids.is_refund_button = True
        if post.get('type') != 'Charge':
            sale_ids.message_post(body=f'Payplus Transaction Number. - {transaction_uid}')
            if sale_ids:
                sale_ids.payplus_payment_status = 'in_payment'
                sale_ids.transaction_number = transaction_uid
                sale_ids.is_warning_div = True
                unconfirmed_sales = sale_ids.filtered(lambda so: so.state in ['draft', 'sent'])
                if unconfirmed_sales:
                    unconfirmed_sales.action_confirm()
                tx.write({
                    'state': 'done',
                })
                tx._handle_notification_data('payplus', post)
                #return request.render('payment_payplus.payplus_success')
        else:
            if tx and not pos_id:
                sale_ids.payplus_payment_status = 'paid'
                sale_ids.message_post(body=f'Payplus Transaction Number. - {transaction_uid}')
                sale_ids.transaction_number = transaction_uid
                tx._handle_notification_data('payplus', post)
            elif tx and  pos_id:
                pos_id.message_post(body=f'Payplus Transaction Number. - {transaction_uid}')
                tx._handle_notification_data('payplus', post)
        # else:
        #     _logger.error("No transaction found for page_request_uid: %s", page_req_uid)
        if sale_ids:
            sale_ids.message_post(body=f"Payplus No. - {post.get('number')}")
        else:
            pos_id.message_post(body=f"Payplus No. - {post.get('number')}")
        return request.redirect('/payment/status')


    @http.route('/payplus/payment/failure', type='http', auth='public', website=True, csrf=False)
    def payplus_payment_failue(self, **post):
        _logger.info("payplus_payment_failue")
        return request.render("payment_payplus.payplus_failure")  
    
class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    payplus_page_req_uid = fields.Char("PayPlus Page Request UID")
    payplus_payment_page_response_json = fields.Json("PayPlus Response Json")
    payplus_payment_success_response_json = fields.Json("PayPlus Payment Success Response Json")

    def _get_tx_from_notification_data(self, provider_code, data):
        tx = super()._get_tx_from_notification_data(provider_code, data)
        if provider_code != 'payplus' or tx:
            return tx
        page_req_uid = data.get('page_request_uid')
        if not page_req_uid:
            raise ValidationError("PayPlus: Missing page_request_uid in response")

        tx = self.search([('payplus_page_req_uid', '=', page_req_uid), ('provider_code', '=', 'payplus')])
        if not tx:
            raise ValidationError(f"PayPlus: No transaction found matching UID {page_req_uid}")
        return tx

    def _process_notification_data(self, data):
        super()._process_notification_data(data)
        if self.provider_code != 'payplus':
            return
        _logger.info("########## _process_notification_data ############ %s", data)
        status = data.get('status')
        self.provider_reference = f"payplus-{self.reference}"
        payment_type = data.get('method') or data.get('brand_name') or ''
        payment_type = payment_type.lower()
        _logger.info("########## payment_type ############ %s", payment_type)
        payment_method_code = const.PAYMENT_METHODS_MAPPING.get(payment_type, 'payplus')
        _logger.info("########## payment_method_code ############ %s", payment_method_code)
        payment_method = self.env['payment.method'].search([('code', '=', payment_method_code),('active','=',True)], limit=1)
        _logger.info("########## payment_method ############ %s , %s", payment_method , payment_method.name)
        if payment_method:
            self.payment_method_id = payment_method
        if status == 'approved':
            self._set_done()
        elif status == 'pending':
            self._set_pending()
        elif status == 'cancel':
            self._set_canceled()
        else:
            self._set_error("Unknown PayPlus status: %s", status)

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'payplus':
            return res
        return processing_values

    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != 'payplus':
            return res
        provider = self.provider_id
        is_test = provider.state == 'test'
        url = 'https://restapidev.payplus.co.il/api/v1.0/' if is_test else 'https://restapi.payplus.co.il/api/v1.0/'
        # url = 'https://restapidev.payplus.co.il/api/v1.0/'
        api_key = provider.test_api_key if is_test else provider.production_api_key
        secret_key = provider.test_secret_key if is_test else provider.production_secret_key
        payment_page_uid = provider.test_page_uid if is_test else provider.production_page_uid
        success_redirect_url = 'payplus/payment/success'
        failed_redirect_url = 'payplus/payment/failure'
        charge_method = self.provider_id.payplus_charge_method
        sendEmailApproval = self.provider_id.send_email_approval
        sendEmailFailure = self.provider_id.send_email_failure
        if not api_key or not secret_key or not payment_page_uid:
            raise ValueError(_("PayPlus credentials are not set. Please check the payment provider configuration."))
        _logger.info("########## getting processing_values ############ %s",processing_values)
        Products = []
        # is_pos_order = False
        name = processing_values['reference']
        if name.startswith('Order'):
            base_ref = '-'.join(name.split('-')[:-1])
            order = self.env['pos.order'].sudo().search([('pos_reference','=',base_ref)])
            charge_method = 1
            # is_pos_order = True
            customer = {
                    "customer_name" : order.partner_id.name or "-",
                    "email" : order.partner_id.email or "-",
                    #"vat_number" : order.partner_id.vat,
                    "phone" : order.partner_id.phone or "-",
                    "address" : order.partner_id.street or "-",
                    "postal_code" : order.partner_id.zip or "-",
                    "city" : order.partner_id.city or "-",
                    "country_iso" : order.partner_id.country_id.code or "IL",
                }
        else:
            order = self.env['sale.order'].sudo().search([('name','=',processing_values['reference'].split('-'))])
            if order:
                customer = {
                    "customer_name" : order.partner_id.name,
                    "email" : order.partner_id.email,
                    #"vat_number" : order.partner_id.vat,
                    "phone" : order.partner_id.phone,
                    "address" : order.partner_id.street,
                    "postal_code" : order.partner_id.zip,
                    "city" : order.partner_id.city,
                    "country_iso" : order.partner_id.country_id.code,
                }
                if order.order_line:
                    for line in order.order_line.filtered(lambda l : l.price_total > 0):
                        if line.tax_id:
                            if line.tax_id.price_include:
                                vat_type = 0
                            else:
                                vat_type = 1
                        else:
                            vat_type = 2
                            
                        Products.append({
                            "name" : line.name,
                            "category_uid" : line.product_id.categ_id.name,
                            "quantity" : line.product_uom_qty,
                            "barcode" : line.product_id.default_code or '',
                            "price" : line.price_total / line.product_uom_qty if line.product_uom_qty else 0.0,
                            "discount_value" : line.discount,
                            "vat_type" :vat_type,
                        })
                
        currenc_code = self.env.company.currency_id.name
        _logger.info("########## getting currency code ############ %s",currenc_code)
        if not currenc_code:
            raise ValueError(_("Currency code is not set. Please check the company configuration."))
    
        headers = {
                "accept": "application/json",
                "api-key": api_key,
                "secret-key": secret_key,
                "content-type": "application/json"
        }
        base_url = self.provider_id.get_base_url()
        payload = {
          "charge_method": charge_method,
          "payment_page_uid": payment_page_uid,
          "sendEmailApproval":sendEmailApproval,
          "sendEmailFailure":sendEmailFailure,
          "expiry_datetime": "5",
          "initial_invoice": True,
          "amount" : processing_values['amount'],
          "currency_code": currenc_code,
          "customer" : customer,
        #   "items" : Products,
          "refURL_success": base_url+success_redirect_url,
          "refURL_failure": base_url+failed_redirect_url,
        }
        _logger.info("########## payplus payload ############ %s", payload)
        _logger.info("########## payplus header ############ %s", headers)
        response = requests.post(f"{url}PaymentPages/generateLink", json=payload, headers=headers)
        _logger.info("########## payplus response ############ %s", response.text)
        response.raise_for_status() 
        result = response.json()
        if result and result['results']['status'] == 'success':
            page_req_uid = result['data']['page_request_uid']
            self.payplus_page_req_uid = page_req_uid
            self.payplus_payment_page_response_json = json.dumps(result)
            redirect_url = result['data']['payment_page_link']
            return {
                "redirect_url": redirect_url
            }
        else:
            raise ValueError(_("Failed to generate PayPlus payment page link."))

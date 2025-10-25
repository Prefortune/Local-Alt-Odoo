# -*- coding: utf-8 -*-

# #############################################################################
# # Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# # Unauthorized copying of this file, via any medium is strictly prohibited
# # Proprietary and confidential
# ##############################################################################

from werkzeug import urls
from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_tranzila.controllers.main import TranzilaController
import requests
import pprint
import logging
import json
_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    def _send_payment_request(self):
        """ Override of payment to send a payment request to Tranzila with a confirmed PaymentToken.
            Note: self.ensure_one()

        :return: None
        :raise: UserError if the transaction is not linked to a token
        """
        super()._send_payment_request()
        if self.provider_code != 'tranzila':
            return
        api_url = 'https://secure5.tranzila.com/cgi-bin/tranzila71u.cgi'
        headersList = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        if self.provider_id:

            payload = {
                'supplier': self.provider_id.token_supplier,
                'TranzilaPW': self.provider_id.token_tranzilaPW,
                'TranzilaTK': self.token_id.provider_ref,
                'sum': self.amount,
                'expdate': self.token_id.expmonth + self.token_id.expyear,
                'reference': self.reference,
                'response_return_format': 'json',
                'ccno': '4557430400000236',
                'myid': '12312312',
                'mycvv': '089',
            }
        else:
            payload = {
                'supplier': self.provider_id.token_supplier,
                'TranzilaPW': self.provider_id.token_tranzilaPW,
                'TranzilaTK': self.token_id.provider_ref,
                'sum': self.amount,
                'expdate': self.token_id.expmonth + self.token_id.expyear,
                'reference': self.reference,
                'response_return_format': 'json'
            }

        response = requests.request("POST", api_url, data=payload, headers=headersList)
        feedback_data = {'response': response.text}
        _logger.info("entering _handle_feedback_data with data:\n%s", pprint.pformat(feedback_data))
        self._handle_notification_data('tranzila', feedback_data)

    _inherit = 'payment.transaction'


    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Tranzila-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'tranzila':
            return res
        if self.sale_order_ids and self.sale_order_ids.payment_limit:
            max_pay = int(self.sale_order_ids.payment_limit)
        elif self.invoice_ids and self.invoice_ids.payment_limit:
            max_pay = int(self.invoice_ids.payment_limit)
        else:
            max_pay = int(self.provider_id.payment_limit)
        partner = self.partner_id
        mobile = partner.mobile or partner.phone
        if self.tokenize:
            if self.provider_id.is_payment:
                api_url = ('https://direct.tranzila.com/' + self.provider_id.token_supplier + '/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s' % (
                self.amount, 1, partner.name, mobile) +'&tranmode=VK&u71=1' + '&cred_type=%s&maxpay=%s'% (8, max_pay))
            else:
                api_url = 'https://direct.tranzila.com/' + self.provider_id.token_supplier + '/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s' % (
                self.amount, 1, partner.name, mobile) +'&tranmode=VK&u71=1'
        else:
            if self.provider_id.is_payment:
                api_url = ('https://direct.tranzila.com/'+ self.provider_id.supplier +'/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s'%(self.amount, 1, partner.name, mobile) + '&cred_type=%s&maxpay=%s' % (8, max_pay))
            else:
                api_url = 'https://direct.tranzila.com/'+ self.provider_id.supplier +'/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s'%(self.amount, 1, partner.name, mobile)


        tranzila_values = {
            'return_url': urls.url_join(self.get_base_url(), TranzilaController._return_url),
            'api_url': api_url,
            'reference': self.reference
        }
        return tranzila_values

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Tranzila data.

        :param str provider_code: The provider of the provider that handled the transaction
        :param dict notification_data: The feedback data sent by the provider
        :return: The transaction if found
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        _logger.info("Response Data with data:\n%s", pprint.pformat(notification_data))
        if provider_code != 'tranzila':
            return tx
        if 'response' in notification_data:
            data_vals = notification_data.get('response')
            data_vals = json.loads(data_vals)
            reference = data_vals.get('reference')
        else:
            reference = notification_data.get('reference')
        if not reference:
            raise ValidationError(
                "Tranzila: " + _(
                    "Received data with missing reference (%(ref)s)",
                    ref=reference,
                )
            )
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'tranzila')])
        tx.ccno = notification_data.get('ccno')
        tx.approved_number = notification_data.get('ConfirmationCode')
        if notification_data.get('cred_type') == '8':
            tx.is_installment = True
            tx.npay = notification_data.get('xnpay')
            tx.fpay = notification_data.get('fpay')
            tx.spay = notification_data.get('spay')
        if not tx:
            raise ValidationError(
                "Tranzila: " + _("No transaction found matching reference %s.", reference)
            )
        return tx
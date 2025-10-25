# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from werkzeug import urls
from odoo import models, fields, _
import json
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_tranzila.controllers.main import TranzilaController
import re


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    transaction_mode = fields.Char('Transaction Mode')
    is_j5_trnsaction = fields.Boolean('Is J5 Transaction')

    def transaction_payment_mode(self, transaction_mode, order_id):
        """
        Sets the transaction mode and marks the POS order as a J5 transaction.

        This method updates the specified POS order with the given transaction mode and
        sets a flag indicating it's processed via the J5 integration.

        Args:
            transaction_mode (str): The payment mode to assign to the POS order (e.g., 'online', 'manual').
            order_id (int): The ID of the POS order (pos.order) to update.

        Returns:
            recordset: The updated pos.order record.
        """
        pos_order = self.env['pos.order'].browse(order_id)
        pos_order.write({'is_j5_transaction' : True})
        return order_id

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Tranzila-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        if self.sale_order_ids and self.sale_order_ids.payment_limit:
            max_pay = int(self.sale_order_ids.payment_limit)
        elif self.invoice_ids and self.invoice_ids.payment_limit:
            max_pay = int(self.invoice_ids.payment_limit)
        else:
            max_pay = int(self.provider_id.payment_limit)
        partner = self.partner_id
        mobile = partner.mobile or partner.phone
        if self.pos_order_id.is_j5_transaction and self.tokenize:
            self.pos_order_id.write({'transaction_mode' : 'j5',
                                     'j5_with_token' : True,})
            partner = self.partner_id
            mobile = partner.mobile or partner.phone
            api_url = ('https://direct.tranzila.com/' + self.provider_id.token_supplier + '/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s' % (
                      self.amount, 1, partner.name,mobile) + '&cred_type=%s' % (1)) + '&tranmode=VK&u71=1'
        else:
            self.pos_order_id.write({'transaction_mode' : None})

            if self.tokenize:
                if self.provider_id.is_payment:
                    api_url = (
                                'https://direct.tranzila.com/' + self.provider_id.token_supplier + '/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s' % (
                            self.amount, 1, partner.name,
                            mobile) + '&tranmode=VK&u71=1' + '&cred_type=%s&maxpay=%s' % (
                                8, max_pay))
                else:
                    api_url = 'https://direct.tranzila.com/' + self.provider_id.token_supplier + '/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s' % (
                        self.amount, 1, partner.name,
                        mobile) + '&tranmode=VK&u71=1'
            else:
                if self.provider_id.is_payment:
                    api_url = (
                                'https://direct.tranzila.com/' + self.provider_id.supplier + '/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s' % (
                        self.amount, 1, partner.name,
                        mobile) + '&cred_type=%s&maxpay=%s' % (8, max_pay))
                else:
                    api_url = 'https://direct.tranzila.com/' + self.provider_id.supplier + '/iframenew.php?sum=%s&currency=%s&lang=il&contact=%s&phone=%s' % (
                    self.amount, 1, partner.name, mobile)
        tranzila_values = {
            'return_url': urls.url_join(self.get_base_url(), TranzilaController._return_url),
            'api_url': api_url,
            'reference': self.reference
        }
        return tranzila_values

    def _set_done(self, state_message=None, extra_allowed_states=()):
        """ Update the transactions' state to `done`.

        :param str state_message: The reason for setting the transactions in the state `done`.
        :param tuple[str] extra_allowed_states: The extra states that should be considered allowed
                                                target states for the source state 'done'.
        :return: The updated transactions.
        :rtype: recordset of `payment.transaction`
        """
        res = super()._set_done(
            state_message,
            extra_allowed_states
            )
        if self.pos_order_id.transaction_mode == 'j5':
            res.state = 'pending'
        else:
            return res

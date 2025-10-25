# -*- coding: utf-8 -*-

from odoo import fields, models, _


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[
            ('pay4all', 'Pay4All (e+)')
        ],
        ondelete={'pay4all': 'set default'}
    )
    
    pay4all_api_key = fields.Char(
        string='API Key',
        help='API Key fornecida pelo Pay4All',
        default='8UmVR3yf7HwBMkNbs6DTDIYdGpOWr7hXVthaqMo30BXSu4WL'
    )
    
    pay4all_account_number = fields.Char(
        string='Account Number',
        help='Número da conta Pay4All',
        default='00375967'
    )
    
    pay4all_notification_token = fields.Char(
        string='Notification Token',
        help='Token para notificações',
        default='QXRSEOAAMOBUOM'
    )

    def _get_supported_currencies(self):
        """ Override to add AOA (Kwanza) support """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'pay4all':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in ['AOA']
            )
        return supported_currencies

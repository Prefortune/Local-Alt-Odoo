# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import models, fields, api, tools, _

TIMEOUT = 60


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Ticket : HT01384
    # Increase the payment limits to 36
    payment_limit = fields.Selection([
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
        ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
        ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
        ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
        ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24'), ('25', '25'),
        ('26', '26'), ('27', '27'), ('28', '28'), ('29', '29'), ('30', '30'),
        ('31', '31'), ('32', '32'), ('33', '33'), ('34', '34'), ('35', '35'),
        ('36', '36')
    ], string="Payment Limit")

    is_tranzila_payment = fields.Boolean('Is Tranzila Payment', compute='_compute_tranzila_payment')

    def _compute_tranzila_payment(self):
        payment_available = self.env['payment.provider'].search([('code', '=', 'tranzila')], limit=1)
        for rec in self:
            if payment_available and payment_available.is_payment:
                rec.is_tranzila_payment = True
            else:
                rec.is_tranzila_payment = False

# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, fields, models


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    transaction_mode = fields.Selection(
        [('normal', 'Normal Transaction'), ('j5', 'J5 Transaction')], 'Transaction Mode',)
    test_is_j5_enabled = fields.Boolean(
        string="Enable J5 Payment (Computed)",
        compute='_compute_j5_enable',
        store=True,
    )

    @api.depends('config_ids.enable_j5_tranzila', 'is_online_payment')
    def _compute_j5_enable(self):
        """
        Computes whether the J5 payment option is enabled for this payment method.

        This method checks if any of the related POS configurations (`config_ids`) have the
        J5 Tranzila integration enabled. It also ensures the payment method is marked as
        an online payment method.

        If both conditions are met, it sets the `test_is_j5_enabled` field to True.

        Computed Field:
            test_is_j5_enabled (bool): True if J5 is enabled in at least one config and
            the payment method is online.
        """
        for payment_method in self:
            # Check if any of the related config_ids have J5 enabled
            has_j5_enabled = any(payment_method.config_ids.mapped('enable_j5_tranzila'))
            payment_method.test_is_j5_enabled = has_j5_enabled and payment_method.is_online_payment

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        add pos payment method field to pos
        """
        fields = super()._load_pos_data_fields(config_id)
        fields += [
            "transaction_mode",
        ]
        return fields

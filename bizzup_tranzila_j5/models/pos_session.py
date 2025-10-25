# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _get_split_receivable_op_vals(self, payment, amount, amount_converted):
        partner = payment.partner_id
        accounting_partner = self.env["res.partner"]._find_accounting_partner(partner)
        if not accounting_partner:
            raise UserError(_("The partner of the POS online payment (id=%d) could not be found", payment.id))
        partial_vals = {
            'account_id': accounting_partner.property_account_receivable_id.id,
            'move_id': self.move_id.id,
            'partner_id': accounting_partner.id,
            'name': '%s - %s (%s)' % (self.name, payment.payment_method_id.name,
                                      payment.online_account_payment_id.payment_method_line_id.payment_provider_id.name),
        }
        return self._debit_amounts(partial_vals, amount, amount_converted)

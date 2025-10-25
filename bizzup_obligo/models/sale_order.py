# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            amount_total = order.amount_total + order.partner_id.obligo
            active_lang = self.env.context.get('lang', 'en_US')

            if amount_total > order.partner_id.credit_limit:
                # Allow if user is in the group OR is the responsible user of the company
                if not (
                        self.env.user.has_group('account.group_account_manager')
                        or self.env.user == self.env.company.user_id
                ):
                    if active_lang == 'he_IL':
                        raise UserError(_('הגבלת אובליגו: רק מנהל חשבונות או משתמש נבחר יכול לאשר את הזמנת הלקוח הנ"ל'))
                    else:
                        raise UserError(
                            _('Obligo limit exceeded: Only an Accounting Manager or the designated approver can approve this order.'))

        return super(SaleOrder, self).action_confirm()

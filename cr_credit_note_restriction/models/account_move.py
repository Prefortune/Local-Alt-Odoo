# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import models, api, _
from odoo.exceptions import AccessError

class AccountMove(models.Model):
    _inherit = 'account.move'


    def create(self, vals):
        if isinstance(vals, list):
            return super().create(vals)

            # Single record creation
        if vals.get('move_type') == 'out_refund' and not self.env.user.has_group('account.group_account_manager'):
            raise AccessError("You are not allowed to create customer credit notes.")

        return super().create(vals)

    def action_post(self):
        print('called')
        print(self.env.user.has_group('account.group_account_manager'))
        for move in self:
            if move.move_type == 'out_refund' and not self.env.user.has_group('account.group_account_manager'):
                raise AccessError(_("Only Accounting Managers can post credit notes."))
        return super(AccountMove, self).action_post()

    def action_switch_move_type(self):
        for move in self:
            # Restrict only regular users from manually switching invoice to credit note
            if not self.env.user.has_group('account.group_account_manager'):
                print(self.env.context)
                if move.move_type == 'out_invoice' and not self.env.context.get('from_sale_credit_note') :
                    raise AccessError(_("You are not allowed to convert an invoice into a credit note."))
        return super().action_switch_move_type()
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False, date=None):
        odoo = self.with_context(from_sale_credit_note=True)
        print("Context at SaleOrder invoice creation: %s", self.env.context)
        return super(SaleOrder, self.with_context(from_sale_credit_note=True))._create_invoices(
            grouped=grouped,
            final=final,
            date=date
        )

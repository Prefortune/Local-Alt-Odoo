# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        for move in self:
            # Only apply the check for customer invoices
            active_lang = self.env.context.get('lang', 'en_US')
            if move.move_type == 'out_invoice' and move.partner_id:
                amount_total = move.amount_total + move.partner_id.obligo
                credit_limit = move.partner_id.credit_limit

                if amount_total > credit_limit:
                    # Allow if user is in the group OR is the responsible user of the company
                    if not (
                        self.env.user.has_group('account.group_account_manager')
                        or self.env.user == self.env.company.user_id
                    ):
                        if active_lang == 'he_IL':
                            raise UserError('הגבלת אובליגו: רק מנהל חשבונות או משתמש נבחר יכול לאשר את החשבונית הנ"ל.')
                        else:
                            raise UserError(_('Obligo limit exceeded: Only an Accounting Manager or the designated approver can approve this Invoice.'))

        # Proceed with the standard action_post
        return super(AccountMove, self).action_post()


    # def _build_credit_warning_message(self, record, current_amount=0.0, exclude_current=False, exclude_amount=0.0):
    #     partner_id = record.partner_id.commercial_partner_id
    #     company = record.company_id
    #
    #     # 🔁 Get company-specific values
    #     partner = partner_id.with_company(company)
    #     credit_to_invoice = partner.credit_to_invoice - exclude_amount
    #     total_credit = partner.obligo + credit_to_invoice + current_amount
    #     obligo = partner.obligo
    #
    #     active_lang = self.env.context.get('lang', 'en_US')
    #
    #     if not obligo or total_credit <= obligo:
    #         return ''
    #
    #     if active_lang == 'he_IL':
    #         msg = _(
    #             '%(partner_name)s השיג את גבול האובליגו של: %(obligo)s',
    #             partner_name=partner.name,
    #             obligo=formatLang(self.env, obligo, currency_obj=company.currency_id)
    #         )
    #     else:
    #         msg = _(
    #             '%(partner_name)s has reached their obligo limit of: %(obligo)s',
    #             partner_name=partner.name,
    #             obligo=formatLang(self.env, obligo, currency_obj=company.currency_id)
    #         )
    #
    #     total_credit_formatted = formatLang(self.env, total_credit, currency_obj=company.currency_id)
    #
    #     if credit_to_invoice > 0 and current_amount > 0:
    #         return msg + '\n' + _(
    #             'Total amount due (including sales orders and this document): %(total_credit)s',
    #             total_credit=total_credit_formatted
    #         )
    #     elif credit_to_invoice > 0:
    #         return msg + '\n' + _(
    #             'Total amount due (including sales orders): %(total_credit)s',
    #             total_credit=total_credit_formatted
    #         )
    #     elif current_amount > 0:
    #         return msg + '\n' + _(
    #             'Total amount due (including this document): %(total_credit)s',
    #             total_credit=total_credit_formatted
    #         )
    #     else:
    #         return msg + '\n' + _(
    #             'Total amount due: %(total_credit)s',
    #             total_credit=total_credit_formatted
    #         )

    def _build_credit_warning_message(self, record, current_amount=0.0, exclude_current=False, exclude_amount=0.0):
        partner_id = record.partner_id.commercial_partner_id
        company = record.company_id

        # 🔁 Get company-specific values
        partner = partner_id.with_company(company)
        credit_to_invoice = partner.credit_to_invoice - exclude_amount
        total_credit = partner.obligo + credit_to_invoice + current_amount
        obligo = partner.obligo

        active_lang = self.env.context.get('lang', 'en_US')

        if not obligo or total_credit <= obligo:
            return ''

        # 🟨 Main warning message
        if active_lang == 'he_IL':
            msg = _(
                '%(partner_name)s הגיע/ה למגבלת האובליגו שלו/שלה: %(obligo)s',
                partner_name=partner.name,
                obligo=formatLang(self.env, obligo, currency_obj=company.currency_id)
            )
        else:
            msg = _(
                '%(partner_name)s has reached their obligo limit of: %(obligo)s',
                partner_name=partner.name,
                obligo=formatLang(self.env, obligo, currency_obj=company.currency_id)
            )

        total_credit_formatted = formatLang(self.env, total_credit, currency_obj=company.currency_id)

        # 🟩 Additional warning lines
        if credit_to_invoice > 0 and current_amount > 0:
            msg_extra = _(
                'Total amount due (including sales orders and this document): %(total_credit)s',
                total_credit=total_credit_formatted
            )
        elif credit_to_invoice > 0:
            msg_extra = _(
                'Total amount due (including sales orders): %(total_credit)s',
                total_credit=total_credit_formatted
            )
        elif current_amount > 0:
            if active_lang == 'he_IL':
                msg_extra = _(
                    'סכום יתרת האובליגו (כולל המסמך הזה) יגיע ל: %(total_credit)s',
                    total_credit=total_credit_formatted
                )
            else:
                msg_extra = _(
                    'Total amount due (including this document): %(total_credit)s',
                    total_credit=total_credit_formatted
                )
        else:
            if active_lang == 'he_IL':
                msg_extra = _(
                    'סכום היתרה: %(total_credit)s',
                    total_credit=total_credit_formatted
                )
            else:
                msg_extra = _(
                    'Total amount due: %(total_credit)s',
                    total_credit=total_credit_formatted
                )

        return msg + '\n' + msg_extra

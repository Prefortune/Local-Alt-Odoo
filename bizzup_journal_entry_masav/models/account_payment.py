# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    masav_entry = fields.Boolean(
        string='Masav Entry',
        default=False,
        copy=False,
        help='Indicates if the Masav journal entry has been created for this payment.')

    def create_journal_entry_for_masav(self, vendor_payments=False,
                                       from_masav_report=False):
        """
        # HT01743
        Create Masav-related journal entries for vendor payments.

        This method performs the following:
        - Filters vendor payments where 'masav_entry' is False.
        - Identifies journal lines with accounts tagged with the special 'shadow' tag
          (account tag: 'bizzup_journal_entry_masav.account_account_tag_for_masav').
        - Groups the payment lines by account, calculates the amount to transfer,
          and creates corresponding journal entries using the 'TMSV' journal.
        - Reconciles original and new journal entry lines on a 1:1 match basis.
        - Sets 'masav_entry' to True for processed payments.

        Behavior:
        - If journal with code 'TMSV' is not found, raises a UserError.
        - If `from_masav_report` is False:
            - Redirects to form view if only one journal entry is created.
            - Redirects to list view if multiple journal entries are created.
        - If `from_masav_report` is True, no redirection is returned.
        :param vendor_payments: Optional recordset of `account.payment` to process.
                            If not provided, uses active_ids context.
        :param from_masav_report: Flag to control redirect behavior and certain validation handling.
        :return: Action dict for UI redirection (if applicable).
        """
        # Filter payments where masav_entry is False
        if not vendor_payments:
            vendor_payments = self.browse(
                self._context.get('active_ids', [])).filtered(
                lambda p: not p.masav_entry)
        if not vendor_payments:
            return

        target_tag = self.env.ref(
            "bizzup_journal_entry_masav.account_account_tag_for_masav")

        journal_id = self.env["account.journal"].search([('code', '=', 'TMSV'),
                                                         ('company_id', '=',
                                                          self.env.company.id)])
        if not journal_id:
            if from_masav_report:
                message = _("No journal found with the code 'TMSV' while creating the "
                  "journal entry for Masav. Please create the journal first with code 'TMSV', "
                  "or alternatively, you can disable the feature in Accounting "
                  "Settings under 'Entry for Payments After Masav' to proceed "
                  "without it.")
            else:
                message = _("No journal found with the code 'TMSV' while creating the "
                  "journal entry for Masav. Please create the journal first with code 'TMSV'.")
            raise UserError(message)

        account_groups = {}
        # Step 1: For each payment, find a journal entry with the account
        # that has the "shadow" tag on it
        masav_entry_payment = self.env["account.payment"]
        for rec in vendor_payments:
            if not rec.move_id:
                continue
            for line in rec.move_id.line_ids:
                account = line.account_id
                if target_tag in account.tag_ids and not line.reconciled:
                    account_id = account.id
                    amount = line.credit - line.debit
                    if amount <= 0:
                        if from_masav_report:
                            break
                        raise UserError(
                            _(f"The payment line is incorrect or already "
                              f"required on payment {rec.name}"))

                    account_groups.setdefault(account_id, []).append({
                        'orig_line': line,
                        'amount': amount,
                        'partner_id': line.partner_id.id,
                    })
                    rec.masav_entry = True
                    masav_entry_payment += rec
                    break

        # Step 2: For each group by account, create a log command
        new_masav_journal_entry_ids = []
        for account_id, items in account_groups.items():
            move_lines = []
            total_amount = 0.0
            for item in items:
                move_lines.append((0, 0, {
                    'account_id': account_id,
                    'partner_id': item['partner_id'],
                    'name': 'Masab',
                    'debit': item['amount'],
                    'credit': 0.0,
                }))
                total_amount += item['amount']

            # Balancing offset line
            move_lines.append((0, 0, {
                'account_id': account_id,
                'name': 'Total offset line',
                'debit': 0.0,
                'credit': total_amount,
            }))

            # Create a log command
            move_id = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'ref': f"Masb offset ({','.join(masav_entry_payment.mapped('name'))})",
                'line_ids': move_lines,
            })

            move_id.action_post()
            new_masav_journal_entry_ids.append(move_id.id)
            # 1:1 match between each payment line and the new obligation line
            new_lines = move_id.line_ids.filtered(
                lambda l: l.account_id.id == account_id and l.debit > 0)

            for item in items:
                orig_line = item['orig_line']
                amount = item['amount']
                matching_line = new_lines.filtered(lambda
                           l: l.debit == amount
                              and l.partner_id.id == orig_line.partner_id.id)
                if matching_line:
                    self.env['account.move.line'].browse(
                        [orig_line.id, matching_line[0].id]).reconcile()
                    orig_line.write({'name': 'Masab'})
                    new_lines -= matching_line[0]
                else:
                    raise UserError(
                        _("No matching row found for amount %.2f for account %s." % (
                            amount, account_id)))

        if new_masav_journal_entry_ids and not from_masav_report:
            if len(new_masav_journal_entry_ids) == 1:
                # Redirect to form view if only one record
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'res_id': new_masav_journal_entry_ids[0],
                    'target': 'current',
                }
            else:
                # Redirect to list view for multiple records
                action = self.env["ir.actions.actions"]._for_xml_id(
                    "account.action_move_journal_line")
                action['domain'] = [
                    ('id', 'in', new_masav_journal_entry_ids)]
                return action
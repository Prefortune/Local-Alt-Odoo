# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo.exceptions import ValidationError
from odoo import api, models, fields, _
from dateutil.relativedelta import relativedelta


class AccountReceiptLine(models.Model):
    """Inherited AccountJournal for customization."""
    _inherit = "lyg.account.receipt.line"

    copy_receipt_line = fields.Boolean('Copy Lines')
    qty_copy = fields.Char('Qty')

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.update({'means_of_payment' : self.journal_id.means_of_payment})

    @api.model
    def create(self, vals_list):
        """Overrides the create method to automatically generate copied
            receipt lines
            if `copy_receipt_line` is enabled and `qty_copy` is specified.
            Args:
                vals_list (dict): Dictionary containing the record values.
            Returns:
                recordset: The newly created `lyg.account.receipt.line` record.
        """
        res = super().create(vals_list)
        if res.copy_receipt_line and res.qty_copy:
            if not res.validity_date:
                raise ValidationError(
                    _('Provide Validity Date to Copy Receipt Line.'))
            res._generate_copy_receipt_lines()

        return res

    def write(self, vals):
        """Overrides the write method to check if `copy_receipt_line` or
         `qty_copy` has been modified and generates new receipt lines
         accordingly.
         Args:
            vals (dict): Dictionary containing updated values for the record.
         Returns:
            bool: True if the write operation is successful.
        """
        res = super().write(vals)
        for record in self:
            if 'copy_receipt_line' in vals or 'qty_copy' in vals:
                if record.copy_receipt_line and record.qty_copy:
                    if not record.validity_date:
                        raise ValidationError(
                            _('Provide Validity Date to Copy Receipt Line.'))
                    record._generate_copy_receipt_lines()
        return res

    def _generate_copy_receipt_lines(self):
        """Generates additional receipt lines based on the `qty_copy` field.
        This method creates new receipt lines with the same payment details,
        increments the validity date for each additional line, and also
        increments `voucher_check_no` for each new line.
        """
        new_lines = []
        base_date = self.validity_date
        base_voucher_check_no = int(
            self.voucher_check_no
            ) if self.voucher_check_no else 0  # Ensure it's an integer

        for i in range(1,int(self.qty_copy)):
            # Create (qty_copy - 1) new lines
            new_vals = {
                'means_of_payment': self.means_of_payment,
                'journal_id': self.journal_id.id,
                'amount': self.amount,
                'branch': self.branch.id if self.branch else False,
                'credit_account_no': self.credit_account_no,
                'bank_id': self.bank_id.id if self.bank_id else False,
                'validity_date': base_date + relativedelta(
                    months=i
                    ),
                'voucher_check_no': str(
                    base_voucher_check_no + i
                    ),  # Increment check number
                'pay_receipt_id': self.pay_receipt_id.id,
            }
            new_lines.append((0, 0, new_vals))

        if new_lines and self.pay_receipt_id:
            # Add new lines correctly
            self.pay_receipt_id.write({'receipt_line_ids': new_lines})

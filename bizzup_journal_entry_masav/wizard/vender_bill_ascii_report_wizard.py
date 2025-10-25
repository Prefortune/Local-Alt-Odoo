# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models


class VenderBillAsciiReportWizard(models.TransientModel):
    _inherit = "vender.bill.ascii.reort.wizard"

    def print_text_report_from_button(self):
        """
        # HT01743
        Override the print button action to optionally create journal entries
        for vendor payments before generating the Masav ASCII report.

        - Checks the configuration setting 'entry_for_payments_after_masav'.
        - If enabled, it finds up to 10 vendor payments where 'masav_entry' is False.
        - Executes the 'create_journal_entry_for_masav' method with those payments.
        - Finally, calls the original method to generate the report.
        :return: Report
        """
        # Check if the setting is enabled
        entry_after_masav = self.env['ir.config_parameter'].sudo().get_param(
            'bizzup_journal_entry_masav.entry_for_payments_after_masav')

        if entry_after_masav:
            # Find vendor payments with masav_entry=False
            vendor_payments = self.env['account.payment'].search([
                ('partner_type', '=', 'supplier'),
                ('masav_entry', '=', False)
            ])
            if vendor_payments:
                # Execute the "Make Journal Entry" server action
                self.env["account.payment"].create_journal_entry_for_masav(
                    vendor_payments, from_masav_report=True)

        # Call the original method
        return super(VenderBillAsciiReportWizard,
                     self).print_text_report_from_button()
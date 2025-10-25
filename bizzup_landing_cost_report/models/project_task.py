# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from datetime import date
from calendar import monthrange

from odoo import models, fields, api, _
from odoo.api import readonly
from odoo.exceptions import ValidationError


def _default_date_from(self):
    """Return the first day of the current month."""
    today = date.today()
    return today.replace(day=1)

def _default_date_to(self):
    """Return the last day of the current month."""
    today = date.today()
    last_day = monthrange(today.year, today.month)[1]
    return today.replace(day=last_day)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    date_from = fields.Date(string=_("Start Date"), default=_default_date_from)
    date_to = fields.Date(string=_("End Date"), default=_default_date_to)
    import_case_id = fields.Many2one(
        "project.task",
        string=_("Import Case"),
        readonly=1,
    )
    company_id = fields.Many2one(
        "res.company",
        string=_("Company"),
        default=lambda self: self.env.company.id,
    )

    def action_generate_landing_cost_report(self):
        """
        Generates the Landing Cost Report wizard for a valid import case.

        This method verifies if the current record is of type 'import_case'.
        If not, it raises a ValidationError. If valid, it returns an action
        dictionary to open the Landing Cost Report wizard with the current
        record's ID prefilled in the context.

        Raises:
            ValidationError: If the record's import_case_type is not 'import_case'.

        Returns:
            dict: An Odoo action dictionary to open the landing cost wizard form view.
        """
        if self.import_case_type != 'import_case':
            raise ValidationError('Only Import Case type are allowed to generate Landing Cost Report')
        else:
            return {
                'name': _('Landing Cost Report'),
                'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'context': {'default_import_case_id': self.id},
                'views': [(self.env.ref('bizzup_landing_cost_report.view_landing_cost_wizard_form', False).id, 'form')],
                'target': 'new',
            }

    def generate_report(self):
        """
          Generates the landing cost report for the selected import case.

          This method performs the following steps:
          - Validates that there are related bills linked to the selected import case.
          - Filters vendor bills (account.move) by invoice date and company within the specified date range.
          - Triggers the XLSX report action `action_report_landing_cost` with the filtered invoice records.

          Raises:
              ValidationError: If no related bills are found on the import case.

          Returns:
              dict: Action dictionary to trigger the XLSX report download.
        """
        self.ensure_one()
        related_bills = self.import_case_id.related_bill_ids

        if not related_bills:
            raise ValidationError(_("There is not any bills!"))

        domain = [
            ("id", "in", related_bills.ids),
            ("invoice_date", ">=", self.date_from),
            ("invoice_date", "<=", self.date_to),
            ("company_id", "=", self.company_id.id)
        ]
        invoice_moves = self.env['account.move'].search(domain)
        if invoice_moves:
            return self.env.ref(
                "bizzup_landing_cost_report.action_report_landing_cost"
            ).report_action(invoice_moves)

# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from datetime import date
from calendar import monthrange

from odoo import api, fields, models, _
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


class LandingCostWizard(models.TransientModel):
    _name = 'landing.cost.wizard'
    _description = 'Landing Cost Report Wizard'

    date_from = fields.Date(string=_("Start Date"), default=_default_date_from)
    date_to = fields.Date(string=_("End Date"), default=_default_date_to)
    import_case_id = fields.Many2one(
        "project.task",
        string=_("Import Case")
    )
    company_id = fields.Many2one(
        "res.company",
        string=_("Company"),
        default=lambda self: self.env.company.id,
    )

    @api.constrains("date_from", "date_to")
    def _check_date_validation(self):
        """
        Constraint to ensure that the Date From is not later
        than the Date To.
        Raises a ValidationError if the condition is violated.
        """
        for rec in self:
            if rec.date_from > rec.date_to:
                raise ValidationError(
                    _("Start Date must be earlier than or equal to End Date.")
                )

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

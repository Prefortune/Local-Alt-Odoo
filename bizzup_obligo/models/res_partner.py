# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta
import io
import xlsxwriter
import base64


class ResPartner(models.Model):
    _inherit = 'res.partner'

    postponed_check_total = fields.Monetary(
        string="Postponed Checks",
        compute="_compute_postponed_check_total",
        store=False,
        currency_field='currency_id'
    )
    obligo = fields.Monetary(
        string="Obligo",
        compute="_compute_obligo",
        store=False,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one('res.currency', string='Currency')
    show_credit_limit = fields.Boolean(compute='_compute_show_credit_limit', store=False)

    @api.depends('company_id')
    def _compute_show_credit_limit(self):
        user = self.env.user
        for rec in self:
            rec.show_credit_limit = user.has_group('account.group_account_manager') or user == user.company_id.user_id

    def _compute_postponed_check_total(self):
        today = date.today()
        for partner in self:
            payments = self.env['account.payment'].search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['paid', 'in_process']),
            ])

            postponed_total = 0.0
            tolerance_days = int(
                float(self.env['ir.config_parameter'].sudo().get_param('bizzup_obligo.credit_tolerance', default=0))
            )

            for payment in payments:
                if payment.validity_date:
                    cutoff_date = payment.validity_date + timedelta(days=tolerance_days)
                    if cutoff_date > today:
                        postponed_total += payment.amount

            partner.postponed_check_total = postponed_total

    def _compute_obligo(self):
        for partner in self:
            partner.obligo = partner.credit + partner.postponed_check_total

    def generate_credit_excel_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        bold = workbook.add_format({'bold': True})

        headers = ['Client Id', 'Client name', 'Credit limit', 'Credit', 'Postponed checks', 'I oblige']

        for partner in self:
            sheet_name = partner.name[:31] if partner.name else f'Partner {partner.id}'  # Sheet name max = 31 chars
            worksheet = workbook.add_worksheet(sheet_name)

            for col, header in enumerate(headers):
                worksheet.write(0, col, header, bold)

            worksheet.write(1, 0, partner.id)
            worksheet.write(1, 1, partner.name)
            worksheet.write(1, 2, partner.credit_limit or 0.0)
            worksheet.write(1, 3, partner.credit or 0.0)
            worksheet.write(1, 4, partner.postponed_check_total or 0.0)
            worksheet.write(1, 5, partner.obligo or 0.0)

        workbook.close()
        output.seek(0)
        report_data = output.read()
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'res_partner_credit_report_by_partner.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(report_data),
            'res_model': 'res.partner',
            'res_id': False,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        download_url = f'/web/content/{attachment.id}?download=true'
        return {
            "type": "ir.actions.act_url",
            "url": download_url,
            "target": "self",
        }

# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api


class RelatedMove(models.Model):
    _name = 'related.move'
    _description = 'Related Move'

    bill_id = fields.Many2one('account.move',"Bill Number")
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='bill_id.company_currency_id')
    company_id = fields.Many2one('res.company', 'Company', related='bill_id.company_id')
    company_currency_id = fields.Many2one(string="Company Currency", related='bill_id.company_id.currency_id')
    task_id = fields.Many2one('project.task', string="Task",)
    invoice_date = fields.Date("Invoice/Bill Date", related='bill_id.invoice_date')
    amount_total_signed = fields.Monetary("Total",currency_field='company_currency_id',related='bill_id.amount_total_signed')
    state = fields.Selection("state",related='bill_id.state')

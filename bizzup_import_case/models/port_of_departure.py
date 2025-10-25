# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api


class PortOfDeparture(models.Model):
    _name = 'port.of.departure'
    _inherits = {'res.partner': 'partner_id'}
    _description = 'Port Of Departure'

    task_id = fields.Many2one('project.task', string="Task",)
    partner_id = fields.Many2one('res.partner',"Contact")
    phone = fields.Char("Phone",related='partner_id.phone')
    complete_name = fields.Char("Phone",related='partner_id.complete_name')
    vat = fields.Char("Tax ID",related='partner_id.vat')
    activity_ids = fields.One2many(
        'mail.activity',string="Activity",related="partner_id.activity_ids")
    company_id = fields.Many2one("res.company",string="Compnay",related='partner_id.company_id')
    pricelist_id = fields.Many2one('product.pricelist', related='partner_id.property_product_pricelist', string='Pricelist')
    country_id = fields.Many2one('res.country',related='partner_id.country_id', string="Country")
    city = fields.Char('City',related='partner_id.city')
    mobile = fields.Char("Mobile",related='partner_id.mobile')
    email = fields.Char("Email",related='partner_id.email')
    user_id = fields.Many2one("res.users", "Salesperson",related='partner_id.user_id',)
    withholding_tax_rate = fields.Float('Withholding Tax Rate', related="partner_id.withholding_tax_rate")

# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    task_id = fields.Many2one('project.task', string='Import Case')
    # partner_id = fields.Many2one('res.partner', string='Contact')
    port_of_departure = fields.Boolean(string='Port of Departure')
    is_port = fields.Boolean(string='Port')

# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api


class RelatedTransfer(models.Model):
    _name = 'related.transfer'
    _description = 'Related Transfer'

    picking_id = fields.Many2one('stock.picking',"Picking")
    task_id = fields.Many2one('project.task', string="Task")
    date_done = fields.Datetime("Date",related='picking_id.date_done')
    scheduled_date = fields.Datetime("Date Scheduled",related='picking_id.scheduled_date')
    state = fields.Selection("state",related='picking_id.state')

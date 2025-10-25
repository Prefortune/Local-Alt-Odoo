# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api


class RelatedStockPikingBatch(models.Model):
    _name = 'related.stock.picking.batch'
    _description = 'Related Stock Picking Batch'

    batch_id = fields.Many2one('stock.picking.batch',"Batch")
    scheduled_date = fields.Datetime(string="Scheduled Date",related='batch_id.scheduled_date')
    task_id = fields.Many2one('project.task', string="Related Task", copy=False)
    seger_number = fields.Char(string="Seger Number",related='batch_id.seger_number')
    size = fields.Char(string="Size",related='batch_id.size')
    ref = fields.Char(string="Reference",related='batch_id.ref')
    picking_ids = fields.One2many('stock.picking','batch_id', "Transfer",related='batch_id.picking_ids')
    state = fields.Selection("state", related='batch_id.state')

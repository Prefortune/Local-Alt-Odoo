# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    import_case_id = fields.Many2one('project.task', string="Related Task", copy=False)
    ref = fields.Char(string="Reference")
    seger_number = fields.Char(string="Seger Number")
    size = fields.Char(string="Size")

    task_id = fields.Many2one(
        'project.task',
        string='Import Case',
    )

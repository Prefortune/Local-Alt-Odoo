# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    import_case_id = fields.Many2one(
        'project.task',
        string='Import Case',
        domain=[('stage_id', '!=', 'done')],
        readonly=False,
        copy=False,
    )
    task_id = fields.Many2one(
        'project.task',
        string='Import Case',
        domain=[('stage_id', '!=', 'done')],
        readonly=False
    )
    import_case_seq = fields.Char('Import Case Sequence', related='import_case_id.import_case_seq')


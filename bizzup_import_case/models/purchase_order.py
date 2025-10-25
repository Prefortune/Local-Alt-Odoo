# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    import_case_ids = fields.Many2many(
        'project.task',
        string="Import Cases",
        compute="_compute_import_case_ids",
        copy=False
    )
    store_case_ids = fields.Many2many(
        'project.task',
        string="Import Cases",
    )
    import_case_seq = fields.Char('Import Case Sequence')

    def _compute_import_case_ids(self):
        for po in self:
            tasks = self.env['project.task']
            seq_list = []

            for picking in po.picking_ids:
                task = picking.import_case_id
                if task:
                    tasks |= task
                    if task.import_case_seq:
                        seq_list.append(task.import_case_seq)

            po.import_case_ids = tasks
            po.store_case_ids = tasks
            po.import_case_seq = ", ".join(seq_list) if seq_list else ""

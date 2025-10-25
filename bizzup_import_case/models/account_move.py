# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    import_case_id = fields.Many2one('project.task', string="Related Task", copy=False)
    bill_id = fields.Many2one('account.move', string="Related Task")
    import_case_seq = fields.Char('Import Case Sequence', related='import_case_id.import_case_seq')

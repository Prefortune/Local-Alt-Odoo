# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup),
# 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact: lg@bizzup.app

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    package_ids = fields.Many2many(
        'stock.quant.package',
        compute='_compute_package_ids',
        string='Packages',
        store=True,
    )

    @api.depends('move_line_ids.result_package_id')
    def _compute_package_ids(self):
        for move in self:
            packages = move.move_line_ids.mapped('result_package_id')
            move.package_ids = packages

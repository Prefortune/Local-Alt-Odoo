# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from datetime import timedelta
from odoo import models, fields, api

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    delivered_in_last_7_days = fields.Boolean(
        string="Delivered in Last 7 Days",
        compute="_compute_delivery_time_flags",
        store=True
    )

    delivered_before_last_7_days = fields.Boolean(
        string="Delivered Before Last 7 Days",
        compute="_compute_delivery_time_flags",
        store=True
    )

    @api.depends('date', 'picking_type_id', 'state')
    def _compute_delivery_time_flags(self):
        """
           Compute flags to identify if a stock move line represents a delivery
           that occurred within the last 7 days or before that.

           Conditions:
           - Only considers stock move lines that are in 'done' state.
           - Only applies to 'outgoing' picking types (deliveries).
           - Compares the move line's date against today's date.

           Sets:
           - delivered_in_last_7_days: True if delivery date is within the last 7 days (inclusive).
           - delivered_before_last_7_days: True if delivery date is older than 7 days.
        """
        today = fields.Date.context_today(self)
        seven_days_ago = today - timedelta(days=7)

        for line in self:
            if (
                line.state == 'done' and
                line.picking_type_id.code == 'outgoing' and
                line.date
            ):
                line_date = line.date.date()
                line.delivered_in_last_7_days = seven_days_ago <= line_date <= today
                line.delivered_before_last_7_days = line_date < seven_days_ago
            else:
                line.delivered_in_last_7_days = False
                line.delivered_before_last_7_days = False

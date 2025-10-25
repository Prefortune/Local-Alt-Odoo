# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, tools
from odoo.tools import float_round


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    task_id = fields.Many2one('project.task', string='Import Case')

    def compute_after_removal(self):
        AdjustmentLines = self.env['stock.valuation.adjustment.lines']
        towrite_dict = {}

        for cost in self.filtered(lambda c: c._get_targeted_move_ids()):
            cost = cost.with_company(cost.company_id)
            rounding = cost.currency_id.rounding
            all_val_line_values = cost.get_valuation_lines()

            # Assign cost_id and cost_line_id to each valuation line value
            for val_line_values in all_val_line_values:
                for cost_line in cost.cost_lines:
                    val_line_values.update({
                        'cost_id': cost.id,
                        'cost_line_id': cost_line.id
                    })

            # Filter existing valuation lines
            valid_lines = cost.valuation_adjustment_lines.filtered(lambda l: not l._origin.id or l.exists())

            for cost_line in cost.cost_lines:
                value_split = 0.0

                # Filter valuation lines for the current cost_line
                relevant_valuations = valid_lines.filtered(lambda v: v.cost_line_id.id == cost_line.id)

                # Identify zero-quantity lines and exclude from distribution
                zero_qty_lines = relevant_valuations.filtered(lambda v: v.quantity == 0)
                relevant_valuations = relevant_valuations - zero_qty_lines

                # Zero out fields for zero-quantity lines
                for zero_line in zero_qty_lines:
                    zero_line.write({
                        'former_cost': 0.0,
                        'additional_landed_cost': 0.0,
                        'final_cost': 0.0
                    })

                # Totals for split calculations
                total_qty = sum(relevant_valuations.mapped('quantity'))
                total_weight = sum(relevant_valuations.mapped('weight'))
                total_volume = sum(relevant_valuations.mapped('volume'))
                total_cost = sum(relevant_valuations.mapped('former_cost'))
                total_line = len(relevant_valuations)

                for valuation in relevant_valuations:
                    value = 0.0

                    if cost_line.split_method == 'by_quantity' and total_qty:
                        value = valuation.quantity * (cost_line.price_unit / total_qty)
                    elif cost_line.split_method == 'by_weight' and total_weight:
                        value = valuation.weight * (cost_line.price_unit / total_weight)
                    elif cost_line.split_method == 'by_volume' and total_volume:
                        value = valuation.volume * (cost_line.price_unit / total_volume)
                    elif cost_line.split_method == 'equal' and total_line:
                        value = cost_line.price_unit / total_line
                    elif cost_line.split_method == 'by_current_cost_price' and total_cost:
                        value = valuation.former_cost * (cost_line.price_unit / total_cost)
                    else:
                        value = cost_line.price_unit / total_line if total_line else 0.0

                    if rounding:
                        value = float_round(value, precision_rounding=rounding, rounding_method='HALF-UP')
                        value_split += value

                    towrite_dict[valuation.id] = towrite_dict.get(valuation.id, 0.0) + value

                # Distribute rounding difference to last valuation
                rounding_diff = cost.currency_id.round(cost_line.price_unit - value_split)
                if not cost.currency_id.is_zero(rounding_diff) and relevant_valuations:
                    towrite_dict[relevant_valuations[-1].id] += rounding_diff

        # Write computed values
        for val_line in AdjustmentLines.browse(towrite_dict.keys()):
            val_line.write({
                'additional_landed_cost': towrite_dict[val_line.id],
                'final_cost': val_line.former_cost + towrite_dict[val_line.id]
            })

        return True

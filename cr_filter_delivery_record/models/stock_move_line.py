# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import models, fields, api
from datetime import datetime, timedelta


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    no_recent_delivery = fields.Boolean(
        string='No Recent Delivery (Last 7 Days)',
        compute='_compute_no_recent_delivery',
        store=True,
        index=True,
    )


    @api.depends('product_id', 'date', 'company_id')
    def _compute_no_recent_delivery(self):
        seven_days_ago = datetime.now() - timedelta(days=7)
        product_ids = list(set(self.mapped('product_id').ids))
        if not product_ids:
            return

        # Group move lines by company to handle multi-company context
        for company in self.mapped('company_id'):
            # Get move lines for the current company
            line = self.env['stock.move.line'].search([('product_id', 'in', product_ids)])
            company_move_lines = line.filtered(lambda l: l.company_id == company)

            # Find recent outgoing move lines for the company
            recent_move_lines = self.env['stock.move.line'].search([
                ('company_id', '=', company.id),
                ('date', '>=', seven_days_ago),
            ])
            products_with_recent_moves = recent_move_lines.mapped('product_id')

            # Process each move line in the company
            for move_line in company_move_lines:
                if (move_line.picking_id and
                        move_line.picking_id.state == 'done' and
                        move_line.picking_id.company_id == company):
                    # Check all products in the same delivery
                    delivery_products = move_line.picking_id.move_line_ids.mapped('product_id')
                    has_recent_move = any(product in products_with_recent_moves for product in delivery_products)
                    move_line.no_recent_delivery = not has_recent_move
                else:
                    move_line.no_recent_delivery = False

        # Handle move lines with no company (if any, though unlikely)
        for move_line in self.filtered(lambda l: not l.company_id):
            move_line.no_recent_delivery = False

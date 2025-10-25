# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from . import models


def _post_init_hook(env):
    """
    Set no_recent_delivery for existing move lines after module install, respecting multi-company rules.
    """
    from datetime import datetime, timedelta

    seven_days_ago = datetime.now() - timedelta(days=7)

    # Get all companies in the database
    companies = env['res.company'].search([])

    for company in companies:
        # Find recent outgoing move lines for the company
        recent_move_lines = env['stock.move.line'].search([
            ('company_id', '=', company.id),
            ('date', '>=', seven_days_ago),
        ])
        products_with_recent_moves = recent_move_lines.mapped('product_id')

        company_move_lines = env['stock.move.line'].search([
            ('company_id', '=', company.id)
        ])

        # Process move lines for the company
        for move_line in company_move_lines:
            if move_line.picking_id.company_id == company:
                # Check all products in the same delivery
                delivery_products = move_line.picking_id.move_line_ids.mapped('product_id')
                has_recent_move = any(product in products_with_recent_moves for product in delivery_products)
                move_line.no_recent_delivery = not has_recent_move
            else:
                move_line.no_recent_delivery = False

    # Handle move lines with no company (if any)
    no_company_move_lines = env['stock.move.line'].search([('company_id', '=', False)])
    for move_line in no_company_move_lines:
        move_line.no_recent_delivery = False


# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app


from odoo import models, fields
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        """
        Validate sub-company receipt. If PO is linked to direct communication,
        confirm SO and run dropshipping flow.
        """
        SaleOrder = self.env['sale.order'].sudo()
        for picking in self:
            po = picking.purchase_id
            if not po or not po.direct_communication:
                continue

            # Find the corresponding Sale Order in the main company
            so = SaleOrder.search([('client_order_ref', '=', po.name), (
            'company_id', '=', po.main_company_id.id)], limit=1)
            if not so:
                raise UserError(
                    f"No Sale Order found in main company for PO {po.name}.")

            # Confirm the Sale Order if not already confirmed
            if so.state in ['draft', 'sent']:
                try:
                    so.action_confirm()
                except Exception as e:
                    raise UserError(
                        f"Failed to confirm the related Sale Order '{so.name}'. "
                        f"Please confirm the Sale Order manually to proceed. "
                        f"Error details: {str(e)}")

            # Dropshipping flow
            try:
                # Get completed picking of sub-company PO
                picking_receipt = self.env['stock.picking'].search(
                    [('purchase_id', '=', po.id)], limit=1)

                # Collect quantity done by product
                receipt_move_qty = {}
                for move in picking_receipt.move_ids:
                    if move.product_id.id not in receipt_move_qty:
                        receipt_move_qty[move.product_id.id] = 0.0
                    receipt_move_qty[move.product_id.id] += move.quantity
                # Get related dropshipping POs from SO
                for dropship_po in so._get_purchase_orders():
                    for dropship_picking in dropship_po.picking_ids.filtered(
                            lambda p: p.state not in ['done', 'cancel']):
                        for move in dropship_picking.move_ids:
                            qty = receipt_move_qty.get(move.product_id.id,
                                                       0.0)
                            if qty > 0:
                                move.quantity = qty
                        dropship_picking.picking_type_id.create_backorder ='never'
                        dropship_picking.button_validate()
                        dropship_picking.picking_type_id.create_backorder ='ask'

            except Exception as e:
                raise UserError(
                    f"Error in dropshipping flow for SO {so.name}: {str(e)}")


        return super().button_validate()

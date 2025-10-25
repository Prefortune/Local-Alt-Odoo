# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api


class AccountMove(models.Model):
    """Inherited AccountMove to add new field and create new picking"""

    _inherit = "account.move"

    is_external_customer_invoice = fields.Boolean(
        "Is External Customer Invoice")

    check_company = fields.Boolean("Check Company",
                                   compute="_compute_check_company")

    @api.depends("company_id")
    def _compute_check_company(self):
        """this method help to check invoice company to hide
        is_external_customer_invoice field"""
        for record in self:
            if ( not record.company_id.is_main or record.move_type !=
                    "out_invoice"):
                record.check_company = True
            else:
                record.check_company = False

    def action_post(self):
        """
        Inherit action_post method to create new picking in main company
        """
        res = super(AccountMove, self).action_post()
        for record in self:
            if record.is_external_customer_invoice:
                company_a_id = 1

                # Find the picking type for outgoing shipments
                picking_type = self.env["stock.picking.type"].search(
                    [("company_id", "=", company_a_id),
                     ("code", "=", "outgoing")],
                    limit=1,
                )

                # Get the default source location
                default_source_location = self.env["stock.location"].search(
                    [
                        ("consignation_locations", "=", True),
                        ("company_id", "=", company_a_id),
                    ],
                    limit=1,
                )

                source = (
                    record.partner_id.consig_location.id
                    if record.partner_id.consig_location
                    else default_source_location.id
                )
                dest_location = picking_type.default_location_dest_id.id

                # Create a new stock picking (transfer)
                picking_vals = {
                    "partner_id": record.partner_id.id,
                    "location_id": source,
                    "location_dest_id": dest_location,
                    "picking_type_id": picking_type.id,
                    "company_id": company_a_id,
                    "move_type": "one",
                }
                new_picking = self.env["stock.picking"].create(picking_vals)

                # Loop through each invoice line to create stock moves
                for invoice_line in record.invoice_line_ids:
                    product = invoice_line.product_id
                    # Create stock move for the product
                    stock_move_vals = {
                        "picking_id": new_picking.id,
                        "product_id": product.id,
                        "quantity": invoice_line.quantity,
                        "name": product.display_name,  # Use product name
                        "location_id": source,
                        "location_dest_id": dest_location,
                        "company_id": company_a_id,
                        "product_uom_qty": invoice_line.quantity,
                        "product_uom": invoice_line.product_uom_id.id,
                    }

                    stock_move = self.env["stock.move"].create(
                        stock_move_vals)

                    lot = invoice_line.lot_id
                    lot_id = False

                    if lot:
                        if lot.product_id.id == product.id and lot.location_id.usage != 'customer':
                            lot_id = lot.id
                            stock_move_line_vals = {
                                'move_id': stock_move.id,
                                "picking_id": new_picking.id,
                                'product_id': product.id,
                                'qty_done': invoice_line.quantity,
                                'product_uom_id': invoice_line.product_uom_id.id,
                                'location_id': source,
                                'location_dest_id': picking_type.default_location_dest_id.id,
                                'company_id': company_a_id,
                                'lot_id': lot_id,
                            }
                            self.env['stock.move.line'].create(
                                stock_move_line_vals)
                # Confirm the picking and validate it
                new_picking.action_assign()
                new_picking.button_validate()

        return res

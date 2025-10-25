# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, SUPERUSER_ID


class StockPicking(models.Model):
    """Inherited Stock Picking"""

    _inherit = "stock.picking"

    def _process_consign_transfer(self):
        """
        Create consignment invoices and transfers.
        """
        is_consign_transfer = self.env[
            "ir.config_parameter"].sudo().get_param("is_consign_transfer")
        if not is_consign_transfer:
            return

        for record in self:
            location_type = record.location_dest_id.usage
            if not (
                    record.state == "done"
                    and location_type == "customer"
                    and record.picking_type_id.code == "outgoing"
            ):
                continue

            owner_company_ids = []
            for stock_move_line in record.move_line_ids.filtered(
                    lambda ml: ml.owner_id.ref_company_ids):
                company_id = self.env["res.company"].sudo().search(
                    [("id", "in",
                      stock_move_line.owner_id.ref_company_ids.ids)],
                    limit=1
                )
                if company_id.is_main and company_id not in owner_company_ids:
                    owner_company_ids.append(company_id)
            for company_id in owner_company_ids:
                # Partners and journal
                partner_in_company_a = self.env["res.partner"].sudo().search(
                    [("ref_company_ids", "in", record.company_id.ids)],
                    limit=1
                )
                if not partner_in_company_a:
                    continue

                journal_id = self.env["account.journal"].sudo().search(
                    [("company_id", "=", company_id.id),
                     ("type", "=", "sale")], limit=1
                )

                invoice = self.env["account.move"].sudo().create(
                    {"partner_id": partner_in_company_a.id,
                     "move_type": "out_invoice",
                     "invoice_date": record.scheduled_date,
                     "company_id": company_id.id, "journal_id": journal_id.id,
                     "pricelist_id": partner_in_company_a.with_company(company_id).property_product_pricelist.id,
                     "narration": "חשבונית למכירות קונסיגנציה", })

                # Picking
                picking_type = self.env["stock.picking.type"].sudo().search(
                    [("company_id", "=", company_id.id),
                     ("code", "=", "outgoing")], limit=1
                )
                default_source_location = self.env[
                    "stock.location"].sudo().search(
                    [("consignation_locations", "=", True),
                     ("company_id", "=", company_id.id)], limit=1
                )
                source = (
                    partner_in_company_a.consig_location.id
                    if partner_in_company_a.consig_location
                    else default_source_location.id
                )

                new_picking = self.env["stock.picking"].sudo().create({
                    "partner_id": partner_in_company_a.id,
                    "location_id": source,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                    "picking_type_id": picking_type.id,
                    "company_id": company_id.id,
                    "move_type": "one",
                })

                for stock_move_line in record.move_line_ids.filtered(
                        lambda ml: company_id in ml.owner_id.ref_company_ids):
                    product = stock_move_line.product_id
                    description = None

                    if stock_move_line.move_id.sale_line_id:
                        sale_order_name = stock_move_line.move_id.sale_line_id.order_id.name
                        description = f"SO: {sale_order_name} - Date: {stock_move_line.move_id.date}"
                    elif stock_move_line.picking_id.pos_order_id and stock_move_line.picking_id.pos_order_id.name:
                        pos_order_name = stock_move_line.picking_id.pos_order_id.name
                        description = f"POS: {pos_order_name} - Date: {stock_move_line.move_id.date}"

                    lot_name = stock_move_line.lot_id.name if stock_move_line.lot_id else None

                    move_line = self.env["account.move.line"].sudo().create({
                        "move_id": invoice.id,
                        "product_id": product.id,
                        "company_id": company_id.id,
                        "quantity": stock_move_line.quantity,
                        "price_unit": product.list_price,
                        "name": description,
                    })
                    lot_id = False
                    if lot_name:
                        lot = self.env["stock.lot"].sudo().search([
                            ("name", "=", lot_name),
                            ("product_id", "=", product.id),
                            ("company_id", "=", company_id.id)
                        ], limit=1)
                        lot_id = lot.id if lot else self.env[
                            "stock.lot"].sudo().create({
                            "name": lot_name,
                            "product_id": product.id,
                            "company_id": company_id.id,
                        }).id

                    stock_line = self.env["stock.move.line"].sudo().create({
                        "picking_id": new_picking.id,
                        "product_id": product.id,
                        "qty_done": stock_move_line.quantity,
                        "product_uom_id": product.uom_id.id,
                        "location_id": source,
                        "location_dest_id": picking_type.default_location_dest_id.id,
                        "company_id": company_id.id,
                        "lot_id": lot_id,
                    })
                invoice.with_user(SUPERUSER_ID).with_context(
                    skip_consign_transfer=True).button_update_prices_from_pricelist()
                invoice.action_post()
                new_picking.action_assign()
                new_picking.with_user(SUPERUSER_ID).with_context(
                    skip_consign_transfer=True).button_validate()

    def button_validate(self):
        """Override to call _process_consign_transfer with safe context"""
        res = super(StockPicking, self).button_validate()
        if not self.env.context.get("skip_consign_transfer"):
            self._process_consign_transfer()
        return res

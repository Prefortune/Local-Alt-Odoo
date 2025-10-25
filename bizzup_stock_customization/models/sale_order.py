# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import fields, models, api


class SaleOrder(models.Model):
    """Inherited Sale Order"""

    _inherit = "sale.order"

    is_so_consig = fields.Boolean("SO Consignment", copy=False)

    check_company = fields.Boolean("Check Company",
                                   compute="_compute_check_company")

    @api.depends("company_id")
    def _compute_check_company(self):
        """this method help to check sale order company to hide
        is_so_consig field"""
        for record in self:
            if record.company_id.is_main:
                record.check_company = False
            else:
                record.check_company = True

    def action_confirm(self):
        """
        Override action_confirm to handle consignment sale orders and
        update picking destination and source locations.
        """
        res = super(SaleOrder, self).action_confirm()

        for order in self:
            partner = order.partner_id
            default_source_location = self.env["stock.location"].sudo().search(
                [
                    ("consignation_locations", "=", True),
                    ("company_id", "=", order.company_id.id),
                ],
                limit=1,
            )
            source_location = partner.consig_location or default_source_location

            matching_po = None
            if order.client_order_ref:
                matching_po = self.env["purchase.order"].sudo().search(
                    [
                        ("company_id", "in", partner.ref_company_ids.ids),
                        ("name", "=", order.client_order_ref),
                    ],
                    limit=1,
                )
                if matching_po and matching_po.is_po_consig:
                    order.is_so_consig = True

            if order.picking_ids and order.is_so_consig and source_location:
                inter_company_location_id = self.env.ref(
                    "stock.stock_location_inter_company"
                ).id

                for picking in order.picking_ids:
                    if picking.location_dest_id.usage == "customer" or picking.location_dest_id.id == inter_company_location_id:
                        picking.location_dest_id = source_location.id
                        picking.note = source_location.name

                    if picking.location_id.usage == "customer" or picking.location_id.id == inter_company_location_id:
                        picking.location_id = source_location.id

                # Update purchase order if matched
                if matching_po:
                    if not matching_po.is_po_consig:
                        matching_po.is_po_consig = True

                    sub_consignation_location = self.env[
                        "stock.location"].sudo().search(
                        [
                            ("consignation_locations", "=", True),
                            ("company_id", "=", matching_po.company_id.id),
                        ],
                        limit=1,
                    )

                    for picking in matching_po.picking_ids:
                        picking.owner_id = matching_po.partner_id.id
                        if sub_consignation_location:
                            picking.location_dest_id = sub_consignation_location.id
                            picking.note = sub_consignation_location.name

        return res

    def _prepare_invoice(self):
        """
        Override _prepare_invoice to update the invoice
        reference based on the matched purchase order.
        """
        res = super(SaleOrder, self)._prepare_invoice()
        purchase_order = self.env['purchase.order'].search(
            [('name', '=', res.get('ref'))], limit=1
        )
        invoice_name = ''
        if purchase_order and purchase_order.invoice_ids:
            invoice_name = purchase_order.invoice_ids[0].name
        res.update({'ref': invoice_name})
        return res

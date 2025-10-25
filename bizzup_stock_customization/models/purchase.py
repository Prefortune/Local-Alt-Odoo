# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import fields, models


class PurchaseOrder(models.Model):
    """Inherited PurchaseOrder"""

    _inherit = "purchase.order"

    # Add a boolean field to indicate if the purchase order is consignment
    is_po_consig = fields.Boolean("Po Consig", copy=False)

    def button_confirm(self):
        """
        Overrides the default `button_confirm` method to add functionality.
        If a purchase order is marked as consignment, the method checks
        if a matching sales order exists. If found, and the sales order
        is not already marked as consignment (`is_so_consig`), it updates
        the sales order to mark it as consignment.
        """
        # Call the parent `button_confirm` method
        res = super(PurchaseOrder, self).button_confirm()

        # Process only orders marked as consignment with relevant partner data
        for order in self.filtered(
            lambda o: o.is_po_consig and o.partner_id
        ):
            # Assign picking owner and update destination location
            for picking in order.picking_ids:
                picking.owner_id = order.partner_id.id

                # Search for a consignment location
                consignation_location = (
                    self.env["stock.location"]
                    .sudo()
                    .search_read(
                        [
                            ("consignation_locations", "=", True),
                            ("company_id", "=", picking.company_id.id),
                        ],
                        limit=1,
                    )
                )
                if consignation_location:
                    picking.write(
                        {
                            "location_dest_id": consignation_location[0].get("id"),
                            "note": consignation_location[0].get("name"),
                        }
                    )

            # Search for a matching sales order in the partner's referenced companies
            matching_so = (
                self.env["sale.order"]
                .sudo()
                .search(
                    [
                        ("client_order_ref", "=", order.name),
                    ],
                    limit=1,
                )
            )
            # If a matching sales order is found, mark it as consignment
            if matching_so and not matching_so.is_so_consig:
                matching_so.write({"is_so_consig": True})

        return res

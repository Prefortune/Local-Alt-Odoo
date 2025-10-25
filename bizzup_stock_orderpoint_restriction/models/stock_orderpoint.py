# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    @api.model
    def create(self, vals):
        """Restrict creation if the main company is not 'is_main=True' and location is consignment."""
        location = self.env['stock.location'].browse(vals.get('location_id'))
        main_company = self.env.user.company_id  # Get the current company
        # Restrict only new records
        if vals.get('location_id') and not main_company.is_main and location.consignation_locations:
            active_lang = self.env.context.get('lang', 'en_US')
            if active_lang == 'he_IL':
                raise ValidationError(
                    (".אתה לא יכול ליצר רענון מלאי עבור מיקום קונסיגנציה כי אתה לא משתמש בחברה ראשית")
                )
            else:
                raise ValidationError(
                    ("You cannot create a stock reorder rule for a consignment location if the main company is not set")
                )
        return super(StockWarehouseOrderpoint, self).create(vals)

    def write(self, vals):
        """Prevent editing of min/max qty for consignment locations and changing to a consignment location."""
        if any(field in vals for field in ['product_min_qty', 'product_max_qty']):
            for rec in self:
                if rec.location_id.consignation_locations:
                    active_lang = self.env.context.get('lang', 'en_US')
                    if active_lang == 'he_IL':
                        raise ValidationError(
                            ("אתה לא רשאי לשנות את כמויות המינ'/מקס' במיקום קונסיגנציה כי אינך משתמש בחברה הראשית.")
                        )
                    else:
                        raise ValidationError(
                            (
                                "You cannot modify minimum or maximum quantity for a consignment location.")
                        )

        if 'route_id' in vals:
            for rec in self:
                if rec.route_id:
                    active_lang = self.env.context.get('lang', 'en_US')
                    if active_lang == 'he_IL':
                        raise ValidationError(
                            ("אתה לא יכול לשנות את המסלול של כלל הרענון במיקום קונסיגנציה.")
                        )
                    else:
                        raise ValidationError(
                            (
                                "You cannot change the route for consignment location.")
                        )

            # Restrict changing of vendor
        if 'supplier_id' in vals:
            for rec in self:
                if rec.vendor_id:
                    active_lang = self.env.context.get('lang', 'en_US')
                    if active_lang == 'he_IL':
                        raise ValidationError(
                            ("אתה לא יכול לשנות את הספק ברענון מלאי במיקום קונסיגנציה.")
                        )
                    else:
                        raise ValidationError(
                            (
                                "You cannot change the vendor for this consignment location.")
                        )


        if 'location_id' in vals:
            new_location = self.env['stock.location'].browse(vals['location_id'])
            for rec in self:
                if not rec.location_id.consignation_locations and new_location.consignation_locations:
                    active_lang = self.env.context.get('lang', 'en_US')
                    if active_lang == 'he_IL':
                        raise ValidationError(
                            ("אתה לא יכול לשנות את המיקום של רענון שבמיקום קונסיגנציה.")
                        )
                    else:
                        raise ValidationError(
                            (
                                "You cannot change the location to a consignment location.")
                        )

        return super().write(vals)


    def action_replenish(self):
        """Override to ensure is_po_consig is set when creating a Purchase Order."""

        # Store relevant data before calling super() to avoid accessing deleted records
        orderpoints_data = {op.name: op.location_id.consignation_locations for op in self}

        res = super().action_replenish()  # Call the original replenish function

        # Ensure we pass a proper list for the domain search
        orderpoint_names = list(orderpoints_data.keys())

        # Find related Purchase Orders created from this orderpoint
        purchase_orders = self.env['purchase.order'].search([
            ('origin', 'in', orderpoint_names)
        ])

        for po in purchase_orders:
            # Directly assign the boolean value from orderpoints_data
            po.is_po_consig = orderpoints_data.get(po.origin, False)
            po.tag_from_transfer = True

        return res  # Return the result after modifying the POs

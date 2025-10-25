# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    direct_communication = fields.Boolean(
        string="Direct Communication",
        copy=False,
        help="If enabled, restricts products to those with direct communication enabled for the vendor.",
    )
    vendor_communication_id = fields.Many2one(
        comodel_name='res.partner',
        string="Vendor for Communication",
        readonly=True,copy=False,
        help="The vendor designated for direct communication."
    )
    main_company_id = fields.Many2one(
        comodel_name='res.company',
        string="Main Company", copy=False,
        domain="[('is_main', '=', True)]",
        help="The main company associated with this purchase order.",
    )
    dropshipping_po = fields.Boolean(
        string="Dropshipping PO",
        copy=False,
        readonly=True,
        invisible=True,
        help="Indicates if this is a dropshipping purchase order."
    )

    def button_confirm(self):
        """
        Custom confirmation logic for Purchase Orders under direct communication flow:
        - Validates that each product has appropriate supplierinfo.
        - Sets vendor_communication_id and switches the partner_id to main company vendor.
        - Handles multi-company restriction by neutralizing company_id on main vendor.
        """
        SupplierInfo = self.env['product.supplierinfo']

        for order in self:
            for line in order.order_line:
                supplier_info = SupplierInfo.search(
                    [('partner_id', '=', order.partner_id.id), (
                        'product_tmpl_id', '=',line.product_id.product_tmpl_id.id),
                     ('company_id','=',order.company_id.id),
                     ('direct_communication','=',True)], limit=1)
                # Error 1: Supplier info missing or product marked as direct — can't create regular PO
                if not supplier_info and order.direct_communication:
                    raise UserError(
                        _("Product '%s' is not configured for direct communication with vendor '%s'.") % (
                            line.product_id.display_name,
                            order.partner_id.display_name))
                # Error 2: Supplier info exists but not marked as direct — can't create regular PO
                if (supplier_info and not order.direct_communication and not
                order.dropshipping_po):
                    raise UserError(
                        _("The user can't create regular PO with products that are defined as direct."))

            # Save current partner as vendor_communication_id
            if order.direct_communication:
                order.vendor_communication_id = order.partner_id
                # Switch to main company vendor as actual PO partner
                main_vendor = order.main_company_id.partner_id
                order.partner_id = main_vendor
        res = super().button_confirm()
        for order in self:
            if order.direct_communication:
                SaleOrder = self.env['sale.order'].sudo()
                so = SaleOrder.search([('client_order_ref', '=', order.name),
                    ('company_id', '=', order.main_company_id.id)], limit=1)
                # Confirm SO if not confirmed
                if so and so.state in ['draft', 'sent']:
                    so.action_confirm()
        # Continue with standard PO confirmation
        return res


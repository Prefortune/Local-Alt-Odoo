# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = "sale.order"

    direct_communication = fields.Boolean(string="Direct Communication",
                                          copy=False)

    def action_confirm(self):
        """
        Confirm sale orders and assign routes.
        Dropshipping flow is triggered only after sub-company receipt.
        """
        dropship_route = self.env.ref('stock_dropshipping.route_drop_shipping')
        PurchaseOrder = self.env['purchase.order'].sudo()

        for sale in self:
            po = PurchaseOrder.search([('name', '=', sale.client_order_ref)], limit=1)
            if not po or not po.direct_communication:
                continue

            sale.direct_communication = True
            sale.order_line.write({'route_id': dropship_route.id})
        res = super().action_confirm()
        for sale in self:
            if not sale.direct_communication:
                continue
            for dropship_po in sale._get_purchase_orders():
                dropship_po.dropshipping_po = True
                if dropship_po.state not in ['purchase', 'done']:
                    dropship_po.button_confirm()
        return res


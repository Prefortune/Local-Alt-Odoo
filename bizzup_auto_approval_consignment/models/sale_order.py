# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, _


class SaleOrder(models.Model):
    """Inherited Sale Order for customization"""
    _inherit = "sale.order"

    def action_confirm(self):
        """
        Overrides the default sale order confirmation behavior.

        If a matching Purchase Order exists in a related company and certain
        synchronization conditions are met (i.e., the document is marked for synchronization
        and the PO is a consignment), the confirmation is skipped.

        Otherwise, the standard confirmation logic is executed.
        """
        for order in self:
            partner = order.partner_id
            matching_po = self.env["purchase.order"].sudo().search(
                [
                    ("company_id", "in", partner.ref_company_ids.ids),
                    ("name", "=", order.client_order_ref),
                ],
                limit=1,
            )
            if matching_po and order.company_id.synchronised_document and matching_po.is_po_consig and self.env.context.get('restrict_access'):
                pass
            else:
                res = super().action_confirm()
                return res

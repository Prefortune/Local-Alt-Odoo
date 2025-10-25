# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    """Inherited SaleOrder for customization."""

    _inherit = "res.partner"

    birthdate = fields.Date("Birthdate")
    mailing_approval = fields.Boolean("Mailing approval")

    delivery_route_id = fields.Many2one("delivery.route", "Delivery Route")

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """only stock manager can edit delivery_route_id field"""
        res = super(ResPartner, self).fields_get(allfields, attributes)
        if not self.env.user.has_group("stock.group_stock_manager"):
            if "delivery_route_id" in res:
                res["delivery_route_id"]["readonly"] = True
        return res

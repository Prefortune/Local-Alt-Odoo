# -*- coding: utf-8 -*-


from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    delivery_route_id = fields.Many2one(
        'delivery.route', string="Delivery Route"
    )

    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            self.delivery_route_id = self.partner_id.delivery_route_id

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """only stock manager and user can edit delivery_route_id field"""
        res = super(SaleOrder, self).fields_get(allfields, attributes)
        stock_user = self.env.user.has_group("stock.group_stock_user")
        stock_manager = self.env.user.has_group("stock.group_stock_manager")

        if not stock_manager and not stock_user:
            if "delivery_route_id" in res:
                res["delivery_route_id"]["readonly"] = True
        return res

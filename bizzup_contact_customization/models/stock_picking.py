# -*- coding: utf-8 -*-


from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_route_id = fields.Many2one(
        'delivery.route', string="Delivery Route"
    )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if res.origin:
            sale_order = self.env['sale.order'].search(
                [('name', '=', res.origin)])
            res.delivery_route_id = sale_order.delivery_route_id
        return res

    @api.onchange("partner_id")
    def _onchange_partner(self):
        """if picking not create form sale order than delivery_route_id
        field value related to partner_id"""
        if not self.sale_id:
            self.delivery_route_id = self.partner_id.delivery_route_id

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """only stock manager can edit delivery_route_id field"""
        res = super(StockPicking, self).fields_get(allfields, attributes)
        if not self.env.user.has_group("stock.group_stock_manager"):
            if "delivery_route_id" in res:
                res["delivery_route_id"]["readonly"] = True
        return res

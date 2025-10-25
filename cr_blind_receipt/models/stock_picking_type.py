# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import models,fields, api, _

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    blind_receipt = fields.Boolean( string="Blind Receipt")

    @api.model
    def can_show_blind_receipt(self, picking_id):
        picking = self.env['stock.picking'].sudo().browse(picking_id)
        picking_type = picking.picking_type_id.sudo()
        if not picking_type.exists():
            return False
        if picking_type.blind_receipt:
            user = self.env.user.sudo()
            group_user = self.env.ref("stock.group_stock_user")
            group_admin = self.env.ref("stock.group_stock_manager")


            if group_user in user.groups_id and group_admin not in user.groups_id:
                return True
            else:
                return False
        return False
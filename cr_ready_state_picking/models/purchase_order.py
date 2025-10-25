# -*- coding: utf-8 -*-
# Part of Creyox Technologies


from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        ref = super().button_confirm()
        if self.picking_ids:
            for picking in self.picking_ids:
                if picking.picking_type_id.warehouse_id.reception_steps == 'one_step':
                    picking.do_unreserve()
        return ref
# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import models, fields,api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()
        if self.state == 'done':
            if self.picking_type_id.warehouse_id.reception_steps == 'one_step':
                self.do_unreserve()
            if self.picking_type_id.warehouse_id.reception_steps == 'two_steps':
                next_transfers = self._get_next_transfers()
                if len(next_transfers) == 1:
                    data = self.env['stock.picking'].search([
                        ('id', '=',next_transfers.id)
                    ])
                    if data:
                        data.do_unreserve()

        return res



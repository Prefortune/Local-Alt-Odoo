# -*- coding: utf-8 -*-
# Part of alt AV ltd. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockMoveInherit(models.Model):
    _inherit = "stock.move.line"

    is_serial = fields.Boolean(string="serial or not")

    def _reservation_is_updatable(self, quantity, reserved_quant):
        self.ensure_one()
        if self.is_serial == True:
            if (self.location_id.id == reserved_quant.location_id.id and
                    self.lot_id.id == reserved_quant.lot_id.id and
                    self.package_id.id == reserved_quant.package_id.id and
                    self.owner_id.id == reserved_quant.owner_id.id):
                return True
            return False
        else:
            # אין super במודל האב, מחזירים False כברירת מחדל
            return False

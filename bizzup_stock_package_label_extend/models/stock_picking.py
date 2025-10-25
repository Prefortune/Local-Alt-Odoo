# -*- coding: utf-8 -*-

from odoo import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_print_picking_barcode(self):
        return self.env.ref('bizzup_stock_package_label_extend.action_report_picking_barcode_smallq').report_action(self)
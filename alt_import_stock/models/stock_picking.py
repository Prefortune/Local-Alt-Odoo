from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def open_stock_move_wizard(self):
        self.ensure_one()
        return {
            'name': 'Import Stock File',
            'type': 'ir.actions.act_window',
            'res_model': 'import.stock.move.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
            }
        } 
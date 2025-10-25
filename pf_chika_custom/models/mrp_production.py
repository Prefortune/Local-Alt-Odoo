from odoo import models, fields

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    pos_order_id = fields.Many2one('pos.order', string='POS Order')

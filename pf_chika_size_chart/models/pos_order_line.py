from odoo import models, fields

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    pf_size_chart_line_ids = fields.One2many(
        'pf.size.chart.line', 'pos_order_line_id', 
        string="Size Chart Lines",
        domain="[('pos_order_line_id', '=', id)]"
    )    
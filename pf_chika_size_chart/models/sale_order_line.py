from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    pf_size_chart_line_ids = fields.One2many(
        'pf.size.chart.line', 'sale_order_line_id', 
        string="Size Chart Lines",
        domain="[('sale_order_line_id', '=', id)]"
    )    
    def action_view_size_chart_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Size Chart Lines',
            'view_mode': 'tree',
            'res_model': 'pf.size.chart.line',
            'domain': [('pf_model', '=', self.product_id.id)],
            'context': dict(self.env.context),
        }
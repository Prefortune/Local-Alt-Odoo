from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    size_chart_ids = fields.One2many('pf.size.chart', 'partner_id', string="Size Charts")
    size_chart_count = fields.Integer(compute='_compute_size_chart_count', string="Size Charts")

    @api.depends('size_chart_ids')
    def _compute_size_chart_count(self):
        for partner in self:
            partner.size_chart_count = self.env['pf.size.chart'].search_count([('partner_id', '=', partner.id)])

    def action_view_size_charts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Size Charts',
            'view_mode': 'tree',
            'res_model': 'pf.size.chart',
            'domain': [('partner_id', '=', self.id)],
            'context': dict(self.env.context),
        }

from odoo import models, fields,api

class SizeChart(models.Model):
    _name = 'pf.size.chart'

    name=fields.Char(string="Name",required=True)
    partner_id=fields.Many2one('res.partner',string="Customer Name")
    pf_date=fields.Date(string="Date")
    pf_invoice=fields.Char(string="Invoice")    
    pf_target_date=fields.Date(string="Target Date")
    pf_status=fields.Selection([('progress','In Progress'),('finished','Finished'),('qc','QC'),('shipped','Shipped')],string="Status")
    pf_model=fields.Many2one('product.product',string="Model")
    pf_new_alter=fields.Char(string="New/Alter")
    pf_fabric=fields.Char(string="Fabric")
    pf_sleeves=fields.Char(string="Sleeves")
    pf_collar=fields.Char(string="Collar")
    pf_closing=fields.Char(string="Closing")
    pf_belt=fields.Char(string="Belt")
    pf_shella=fields.Char(string="Shella")
    pf_body_size=fields.Char(string="Body Size (UK/...)")
    pf_note=fields.Char(string="Note")
    pf_length=fields.Float(string="Length")
    pf_shoulder=fields.Float(string="Shoulders")
    pf_sleeves=fields.Float(string="Sleeves")
    pf_underarm=fields.Float(string="UnderArm")
    pf_upperarm=fields.Float(string="Upper Arm")
    pf_chest=fields.Float(string="Chest")
    pf_hips=fields.Float(string="Hips")
    pf_waist=fields.Float(string="Waist")
    pf_pocket_height=fields.Float(string="Pocket Height")
    total_quantity = fields.Float(string="Total Quantity", compute="_compute_total_quantity")
    size_chart_line_ids = fields.One2many('pf.size.chart.line', 'size_chart_id', string="Size Chart Lines")


    @api.depends('size_chart_line_ids.quantity')
    def _compute_total_quantity(self):
        for record in self:
            record.total_quantity = sum(line.quantity for line in record.size_chart_line_ids)
    def action_view_order_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Sale Order Lines',
            'view_mode': 'tree',
            'res_model': 'pf.size.chart.line',          
            'domain': [
                ('size_chart_id', 'in',[self.id]),
                ('pf_model', '=', self.pf_model.id),
            ],
            'context': dict(self.env.context),
        }

class SizeChartLine(models.Model):
    _name = 'pf.size.chart.line'
    _description = 'Size Chart Line'

    @api.model
    def default_get(self, fields_list):
        """ Automatically fill Sale Order Line ID and Product ID """
        res = super(SizeChartLine, self).default_get(fields_list)
        context = self.env.context

        if context.get('default_sale_order_line_id') and res.get('name'):
            sale_order_line = self.env['sale.order.line'].browse(context['default_sale_order_line_id'])
            res['sale_order_line_id'] = sale_order_line.id
            res['pf_model'] = sale_order_line.product_id.id

            #create default size chart with customer if not exists
            if not res.get('size_chart_id'):
                size_chart = self.env['pf.size.chart'].create({
                    'name': res.get('name'),
                    'partner_id': sale_order_line.order_id.partner_id.id,
                })
                res['size_chart_id'] = size_chart.id
        
        return res
    
    name = fields.Char(string="Name")
    size_chart_id = fields.Many2one('pf.size.chart', string="Size Chart",required=True)
    quantity = fields.Float(string="Quantity", required=True,default=1)
    pf_model=fields.Many2one('product.product',string="Model")
    sale_order_line_id=fields.Many2one('sale.order.line',string="Sale Order Line")
    pos_order_line_id=fields.Many2one('pos.order.line',string="Pos Order Line")

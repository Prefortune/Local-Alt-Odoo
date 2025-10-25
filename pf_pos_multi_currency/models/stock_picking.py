from odoo import models,fields,api

class StockPicking(models.Model):
    _inherit = "stock.picking"


    pf_mrp_order_ids=fields.One2many('mrp.production','pf_stock_picking_id',string="Altration")
    pf_mrp_count=fields.Integer(string="Manufacturing",compute="_compute_mrp_count")

    @api.depends('pf_mrp_order_ids')
    def _compute_mrp_count(self):
        for rec in self:            
            if rec.pf_mrp_order_ids:
                rec.pf_mrp_count=len(rec.pf_mrp_order_ids.ids)
            else:
                rec.pf_mrp_count=0


    def GenrateProduction(self):        
        if self.move_ids_without_package:            
            altration_location=self.env['stock.location'].sudo().search([('pf_stock_altration','=',True)],limit=1)
            # print("\n\n\n........altration_obj....",altration_location)
            if  altration_location:
                for move in self.move_ids_without_package:
                    if move.product_id:                    
                        mrp_obj=self.env['mrp.production'].sudo().create({
                                'product_id':move.product_id.id,
                                'product_qty':move.product_uom_qty,
                                'pf_stock_picking_id':self.id,                               
                                'move_raw_ids':[(0,0,{'product_id':move.product_id.id,'location_id':move.location_id.id,'product_uom_qty':move.product_uom_qty,})]
                        })
                        mrp_obj.write({
                            'bom_id':self.env['mrp.bom'],
                            'location_src_id':self.location_id.id,
                            'location_dest_id':altration_location.id,
                        })
                # print("\n\\nn.......................before,,,,",move.location_id)
                self.sudo().write({
                    'location_id':altration_location.id
                })
                # print("\n\\nn.......................after,,,,",move.location_id)

    def action_view_mrp(self):       
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            "domain": [('id', 'in', self.pf_mrp_order_ids.ids)],            
            'view_mode': 'tree,form'
        }
   

class MrpProduction(models.Model):
    _inherit="mrp.production"

    pf_stock_picking_id=fields.Many2one('stock.picking',string="Stock Picking")
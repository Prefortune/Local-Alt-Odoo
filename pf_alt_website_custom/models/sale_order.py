from odoo import fields, models,api
import logging
_logger = logging.getLogger(__name__)

class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()

        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']

        for order in self:
            for line in order.order_line:
                if line.product_id.detailed_type == 'bundle' and line.product_id.product_bundle_ids:
                    picking = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])
                    group_id = line._get_procurement_group()
                    if not group_id:
                        group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                        line.order_id.procurement_group_id = group_id
                    if picking:
                        picking = picking[0]
                    else:
                        vals = {
                            'partner_id': order.partner_id.id,
                            'picking_type_id': order.warehouse_id.out_type_id.id,
                            'location_id': order.warehouse_id.lot_stock_id.id,
                            'location_dest_id': order.partner_id.property_stock_customer.id,
                            'origin': order.name,
                        }
                        picking = StockPicking.create(vals)
                        _logger.info("picking order id -- %s %s",picking.name,picking.sale_id)
                       
                    for bundle_line in line.product_id.product_bundle_ids:
                        StockMove.create({
                            'name': bundle_line.product_id.display_name,
                            'product_id': bundle_line.product_id.id,
                            'product_uom_qty': line.product_uom_qty,
                            'product_uom': bundle_line.product_id.uom_id.id,
                            'picking_id': picking.id,
                            'location_id': picking.location_id.id,
                            'location_dest_id': picking.location_dest_id.id,
                            'company_id': order.company_id.id,
                            'picking_type_id': picking.picking_type_id.id,
                            'sale_line_id': line.id,
                            'group_id' : group_id.id
                        })
                    picking.action_confirm()
        return res

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPicking,self).button_validate()
        if self.sale_id:
            sale_order = self.sale_id
            filter_bundel_product = sale_order.order_line.filtered(lambda x:x.product_template_id.detailed_type == 'bundle')
            if filter_bundel_product:
                for filter in filter_bundel_product:
                    order_qty = filter.product_uom_qty
                    filter.qty_delivered = order_qty
        return res
  
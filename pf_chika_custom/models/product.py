from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    min_variant_price = fields.Float(string="Min Variant Price", compute="_compute_variant_price_range", store=True)
    max_variant_price = fields.Float(string="Max Variant Price", compute="_compute_variant_price_range", store=True)

    @api.depends('product_variant_ids', 'product_variant_ids.lst_price')
    def _compute_variant_price_range(self):
        for template in self:
            prices = template.product_variant_ids.mapped('lst_price')
            template.min_variant_price = min(prices) if prices else 0.0
            template.max_variant_price = max(prices) if prices else 0.0
            _logger.info("Computed min and max variant prices for product template %s: min=%s, max=%s",
                         template.id, template.min_variant_price, template.max_variant_price)

class PosSessionInherit(models.Model):
    _inherit = "pos.session"

    invoice_id = fields.Many2one('account.move', string='Session Invoice')

    def action_open_invoice_wizard(self):
        return {
            'name' : 'Create invoice for merchant',
            'type': 'ir.actions.act_window',
            'res_model': 'pos.session.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_session_id': self.id,
            },
        }

    def action_view_session_invoice(self):
        self.ensure_one()
        if self.invoice_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': self.invoice_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('min_variant_price')
        result['search_params']['fields'].append('max_variant_price')
        return result
    
    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        result += ['product.product']
        return result

    def action_pos_session_close(self, *args, **kwargs):
        for session in self:
            session._create_mo_for_orders()
        return super().action_pos_session_close(*args, **kwargs)

    
    def _create_mo_for_orders(self):
        # Track virtual available qty for each product
        virtual_qty = {}
        for order in self.order_ids:
            for line in order.lines:
                product = line.product_id
                if product.type == 'product' and not order.checked_mrp_production:
                    
                    if product.id not in virtual_qty:
                        virtual_qty[product.id] = product.qty_available
                    available_qty = virtual_qty[product.id]
                    _logger.info("Processing order %s for product %s with available qty %s", order.name, product.name, available_qty)
                    _logger.info("Order line quantity: %s", line.qty)
                    if available_qty < line.qty:
                        mo_qty = line.qty - available_qty
                        mo = self.env['mrp.production'].create({
                            'product_id': product.id,
                            'product_qty': mo_qty,
                            'product_uom_id': product.uom_id.id,
                            'origin': order.name,
                            'pos_order_id': order.id,
                        })
                        virtual_qty[product.id] = 0
                    else:
                        virtual_qty[product.id] -= line.qty
            order.checked_mrp_production = True

class PosOrder(models.Model):
    _inherit = 'pos.order'

    mrp_production_ids = fields.One2many('mrp.production', 'pos_order_id', string='Manufacturing Orders')
    mrp_production_count = fields.Integer(string='MO Count', compute='_compute_mrp_production_count')
    checked_mrp_production = fields.Boolean(string='Checked MO', default=False)

    def _compute_mrp_production_count(self):
        for order in self:
            order.mrp_production_count = len(order.mrp_production_ids)

    def action_view_mrp_productions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Orders',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('pos_order_id', '=', self.id)],
            'context': dict(self.env.context),
        }
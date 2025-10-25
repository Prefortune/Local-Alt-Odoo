from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import logging
_logger = logging.getLogger(__name__)


class SplitDeliveryPortal(http.Controller):

    @http.route(['/my/orders/<int:order_id>/split_delivery'], type='http', auth="user", website=True)
    def show_split_delivery_page(self, order_id, **kwargs):
        order = request.env['sale.order'].sudo().browse(order_id)

        user_partner = request.env.user.partner_id

        # Allow if user is the order partner OR the parent of the order partner
        if user_partner.id not in [order.partner_id.id, order.partner_id.parent_id.id]:
            raise AccessDenied()

        countries = request.env['res.country'].sudo().search([])

        # Prepare existing deliveries (based on stock.picking origin)
        delivery_data = {}

        existing_pickings = order.picking_ids.filtered(lambda p: 'Split #' in (p.origin or ''))
        for picking in existing_pickings:
            try:
                index = int(picking.origin.split('#')[-1]) - 1
            except Exception:
                continue

            # Build move data per sale_line_id
            moves_data = {}
            for move in picking.move_ids.filtered(lambda m: m.sale_line_id):
                moves_data[move.sale_line_id.id] = {
                    'quantity': move.product_uom_qty,
                    'move_id': move.id,
                }

            delivery_data[index] = {
                'picking_id': picking.id,
                'partner_id': picking.partner_id.id,
                'street': picking.partner_id.street,
                'street2': picking.partner_id.street2,
                'city': picking.partner_id.city,
                'zip': picking.partner_id.zip,
                'country_id': picking.partner_id.country_id.id,
                'moves': moves_data,
                'is_done': picking.state == 'done',
            }

        return request.render('alt_split_delivery.split_delivery_page', {
            'order': order,
            'countries': countries,
            'delivery_data': delivery_data,
        })


    @http.route(['/my/orders/<int:order_id>/split_delivery/save'], type='http', auth="user", website=True, methods=['POST'])
    def save_split_delivery(self, order_id, **post):
        order = request.env['sale.order'].sudo().browse(order_id)
        user_partner = request.env.user.partner_id

        # Allow if user is the order partner OR parent of the order partner
        if user_partner.id not in [order.partner_id.id, order.partner_id.parent_id.id]:
            raise AccessDenied()

        
        # ❗ Delete default delivery pickings (not custom split ones)
        default_pickings = order.picking_ids.filtered(
            lambda p: not p.origin or not p.origin.startswith(f"{order.name} - Split #")
        )
        default_pickings.sudo().unlink()

        warehouse = order.warehouse_id or request.env['stock.warehouse'].sudo().search([], limit=1)
        count = int(post.get('count', 0))
        product_lines = order.order_line.filtered(lambda l: l.product_id.type != 'service')

        for i in range(count):
            # Get or create partner address
            partner_id = post.get(f'partner_id_{i}')
            if partner_id:
                partner = request.env['res.partner'].sudo().browse(int(partner_id))
            else:
                partner = request.env['res.partner'].sudo().create({
                    'parent_id': order.partner_id.id,
                    'type': 'delivery',
                    'street': post.get(f'street_{i}', ''),
                    'street2': post.get(f'street2_{i}', ''),
                    'city': post.get(f'city_{i}', ''),
                    'zip': post.get(f'zip_{i}', ''),
                    'country_id': int(post.get(f'country_id_{i}', 0)) or False,
                })

            # Get or create the picking
            picking_id = post.get(f'picking_id_{i}')
            if picking_id:
                picking = request.env['stock.picking'].sudo().browse(int(picking_id))
                picking.write({'partner_id': partner.id})
            else:
                picking = request.env['stock.picking'].sudo().create({
                    'partner_id': partner.id,
                    'picking_type_id': warehouse.out_type_id.id,
                    'location_id': warehouse.lot_stock_id.id,
                    'location_dest_id': partner.property_stock_customer.id,
                    'origin': f"{order.name} - Split #{i + 1}",
                    'sale_id': order.id,
                })

            # Map of existing moves by sale_line_id
            existing_moves = {move.sale_line_id.id: move for move in picking.move_ids if move.sale_line_id}

            # Loop through product lines and update/create moves
            for line in product_lines:
                qty_str = post.get(f'quantity_{i}_{line.id}')
                if not qty_str:
                    continue
                try:
                    qty = float(qty_str)
                except ValueError:
                    qty = 0.0

                if qty <= 0:
                    continue

                if line.id in existing_moves:
                    existing_moves[line.id].sudo().write({'product_uom_qty': qty})
                else:
                    request.env['stock.move'].sudo().create({
                        'picking_id': picking.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': qty,
                        'product_uom': line.product_uom.id,
                        'name': line.name,
                        'location_id': warehouse.lot_stock_id.id,
                        'location_dest_id': partner.property_stock_customer.id,
                        'sale_line_id': line.id,
                    })

            # Optional: Confirm & assign picking (if auto-handling is needed)
            # picking.action_confirm()
            # picking.action_assign()

        return request.redirect(f'/my/orders/{order.id}')



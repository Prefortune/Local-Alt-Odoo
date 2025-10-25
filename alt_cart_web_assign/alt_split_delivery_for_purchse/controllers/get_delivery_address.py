from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import logging
_logger = logging.getLogger(__name__)
import re

class SplitDeliveryController(http.Controller):

    @http.route(['/my/orders/<int:order_id>/split_delivery'], type='http', auth="user", website=True)
    def show_split_delivery_page(self, order_id, **kwargs):
        order = request.env['sale.order'].sudo().browse(order_id)

        order_company_id = order.company_id.id
        website_id = request.env['website'].search([('company_id','=',order_company_id)],limit=1)
        _logger.info("888888888888888888 website_id 88888888888888888888 %s",website_id)
        request.website = website_id

        user_partner = request.env.user.partner_id
        request_user = request.env.user
        # if user_partner.id not in [order.partner_id.id, order.partner_id.parent_id.id]:
        #     raise AccessDenied()

        if not (
            request_user.has_group('sales_team.group_sale_manager') or
            user_partner.id in [order.partner_id.id, order.partner_id.parent_id.id]
        ):
            raise AccessDenied()

        countries = request.env['res.country'].sudo().search([])
        Israel = request.env['res.country'].sudo().search([('code', '=', 'IL')], limit=1)
        _logger.info(" ------------- Israel getting ------------ %s %s",Israel , Israel.name)
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
                'moves': moves_data,
                'is_done': picking.state == 'done',
            }

        return request.render('alt_split_delivery.split_delivery_page', {
            'order': order,
            'countries': countries,
            'delivery_data': delivery_data,
            'website': website_id,

        })


    @http.route(['/my/orders/<int:order_id>/split_delivery/save'], type='http', auth="user", website=True, methods=['POST'])
    def save_split_delivery(self, order_id, **post):
        
        # _logger.info("my/orders/<int:order_id>/split_delivery/save is called --------- %s",post)
        print(" - post data - ",post)
        form_json = post
        order = request.env['sale.order'].sudo().browse(order_id)

        order_company_id = order.company_id.id
        website_id = request.env['website'].search([('company_id','=',order_company_id)],limit=1)
        _logger.info("888888888888888888 website_id 88888888888888888888 %s",website_id)
        request.website = website_id

        # if order.partner_id.id != request.env.user.partner_id.id:
        #     raise AccessDenied()

        request_user = request.env.user
        user_partner = request.env.user.partner_id

        if not (
            request_user.has_group('sales_team.group_sale_manager') or
            user_partner.id in [order.partner_id.id, order.partner_id.parent_id.id]
        ):
            raise AccessDenied()

        ordered_qty_map = {
            str(line.id): line.product_uom_qty
            for line in order.order_line.filtered(lambda l: l.product_id.type != 'service')
        }
        
        # _logger.info("Ordered Qty Map ------------------- : %s", ordered_qty_map)
        print(" - order data - ", ordered_qty_map)

         # Build assigned quantity map from dynamic keys
        assigned_qty_map = {}
        # pattern = re.compile(r'product_name_(\d+)_(\d+)')  # matches product_name_i_lineid
        pattern = re.compile(r'quantity_(\d+)_(\d+)')  
        for key, qty_str in form_json.items():
            match = pattern.match(key)
            if match:
                i = match.group(1)
                line_id = match.group(2)
                try:
                    qty = float(qty_str)
                    assigned_qty_map[line_id] = assigned_qty_map.get(line_id, 0.0) + qty
                except ValueError:
                    continue

        _logger.info("Assigned Qty Map: %s", assigned_qty_map)   

        error_messages = []
        for line_id, ordered_qty in ordered_qty_map.items():
            assigned_qty = assigned_qty_map.get(line_id, 0.0)
            if assigned_qty > ordered_qty:
                product = order.order_line.browse(int(line_id)).product_id.display_name
                error_messages.append(f"❌ For '{product}', assigned more than ordered. Ordered: {ordered_qty}, Assigned: {assigned_qty}")
            elif assigned_qty < ordered_qty:
                product = order.order_line.browse(int(line_id)).product_id.display_name
                error_messages.append(f"⚠️ For '{product}', assigned less than ordered. Ordered: {ordered_qty}, Assigned: {assigned_qty}")
        
        if error_messages:
            return request.render("alt_split_delivery.split_delivery_error_page", {
                'error_messages': error_messages,
                'order': order_id,
                'website': website_id,
            })
        else:
            # return False
            # ❗ Delete default delivery pickings (not custom split ones)
            default_pickings = order.picking_ids.filtered(
                lambda p: not p.origin or not p.origin.startswith(f"{order.name} - Split #")
            )
            default_pickings.sudo().unlink()

            warehouse = order.warehouse_id or request.env['stock.warehouse'].sudo().search([], limit=1)
            count = int(post.get('count', 0))
            product_lines = order.order_line.filtered(lambda l: l.product_id.type != 'service')
            israel = request.env['res.country'].sudo().search([('code', '=', 'IL')], limit=1)

            for i in range(count):
                picking_status = post.get(f'picking_status_{i}')
                if picking_status:
                    continue
                # Get or create partner address
                partner_id = post.get(f'partner_id_{i}')
                if partner_id:
                    partner = request.env['res.partner'].sudo().browse(int(partner_id))
                    partner.write({
                        'street': post.get(f'street_{i}', ''),
                        'street2': post.get(f'street2_{i}', ''),
                        'city': post.get(f'city_{i}', ''),
                        'zip': post.get(f'zip_{i}', ''),
                    })
                else:
                    partner = request.env['res.partner'].sudo().create({
                        'parent_id': order.partner_id.id,
                        'type': 'delivery',
                        'street': post.get(f'street_{i}', ''),
                        'street2': post.get(f'street2_{i}', ''),
                        'city': post.get(f'city_{i}', ''),
                        'zip': post.get(f'zip_{i}', ''),
                        # 'country_id': int(post.get(f'country_id_{i}', 0)) or False,
                        'country_id': israel.id,
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
            return request.redirect(f'/my/orders/{order.id}')
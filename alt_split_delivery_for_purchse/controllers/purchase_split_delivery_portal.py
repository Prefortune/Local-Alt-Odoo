from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import logging
_logger = logging.getLogger(__name__)
import re

class PurchaseSplitDeliveryPortal(http.Controller):

    @http.route(['/my/purchase/orders/<int:order_id>/split_delivery'], type='http', auth="user", website=True)
    def show_purchase_split_delivery_page(self, order_id, **kwargs):
        order = request.env['purchase.order'].sudo().browse(order_id)
        
        # בדיקת הרשאות - רק מנהלי רכש
        if not request.env.user.has_group('purchase.group_purchase_manager'):
            raise AccessDenied()
        
        # הכנת נתוני המנות הקיימות
        delivery_data = {}
        existing_pickings = order.picking_ids.filtered(lambda p: 'מנה' in (p.origin or ''))
        
        for picking in existing_pickings:
            try:
                # חילוץ מספר המנה מה-origin
                index = int(picking.origin.split('מנה')[-1].strip()) - 1
            except Exception:
                continue

            # נתוני הכתובת
            delivery_data[index] = {
                'picking_id': picking.id,
                'partner_id': picking.partner_id.id,
                'street': picking.partner_id.street,
                'street2': picking.partner_id.street2,
                'city': picking.partner_id.city,
                'zip': picking.partner_id.zip,
                'country_id': picking.partner_id.country_id.id,
                'is_done': picking.state == 'done',
            }

        return request.render('alt_split_delivery.purchase_split_delivery_page', {
            'order': order,
            'delivery_data': delivery_data,
        })

    @http.route(['/my/purchase/orders/<int:order_id>/split_delivery/save'], type='http', auth="user", website=True, methods=['POST'])
    def save_purchase_split_delivery(self, order_id, **post):
        order = request.env['purchase.order'].sudo().browse(order_id)
        
        # בדיקת הרשאות
        if not request.env.user.has_group('purchase.group_purchase_manager'):
            raise AccessDenied()
        
        # מחיקת pickings ברירת מחדל (לא מנות)
        default_pickings = order.picking_ids.filtered(
            lambda p: not p.origin or 'מנה' not in p.origin
        )
        default_pickings.sudo().unlink()

        warehouse = order.warehouse_id or request.env['stock.warehouse'].sudo().search([], limit=1)
        count = int(post.get('count', 0))
        product_lines = order.order_line.filtered(lambda l: l.product_id.type != 'service')
        israel = request.env['res.country'].sudo().search([('code', '=', 'IL')], limit=1)

        for i in range(count):
            # בדיקה אם המנה כבר קיימת
            picking_status = post.get(f'picking_status_{i}')
            if picking_status:
                continue
                
            # קבלת או יצירת כתובת
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
                    'country_id': israel.id,
                })

            # קבלת או יצירת picking
            picking_id = post.get(f'picking_id_{i}')
            if picking_id:
                picking = request.env['stock.picking'].sudo().browse(int(picking_id))
                picking.write({'partner_id': partner.id})
            else:
                picking = request.env['stock.picking'].sudo().create({
                    'partner_id': partner.id,
                    'picking_type_id': warehouse.in_type_id.id,  # Incoming
                    'location_id': partner.property_stock_supplier.id,
                    'location_dest_id': warehouse.lot_stock_id.id,
                    'origin': f"{order.name} - מנה {i + 1}",
                    'purchase_id': order.id,
                })

            # עדכון moves לפי כמויות
            existing_moves = {move.product_id.id: move for move in picking.move_ids}

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

                if line.product_id.id in existing_moves:
                    existing_moves[line.product_id.id].sudo().write({'product_uom_qty': qty})
                else:
                    request.env['stock.move'].sudo().create({
                        'picking_id': picking.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': qty,
                        'product_uom': line.product_uom.id,
                        'name': line.name,
                        'location_id': partner.property_stock_supplier.id,
                        'location_dest_id': warehouse.lot_stock_id.id,
                    })

        return request.redirect(f'/my/purchase/orders/{order.id}')

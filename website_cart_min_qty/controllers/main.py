# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleMinQty(WebsiteSale):

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        """Override to validate minimum quantity before adding to cart"""
        result = super().cart_update_json(product_id, line_id, add_qty, set_qty, display)
        
        # Get product template
        product = request.env['product.template'].browse(product_id)
        
        # Check if product has minimum quantity enabled
        if product.website_min_qty_enabled:
            min_qty = product.website_min_qty
            current_qty = result.get('quantity', 0)
            
            if current_qty < min_qty:
                return {
                    'status': 'error',
                    'message': f'Minimum quantity for {product.name} is {min_qty}. Please add at least {min_qty} items.',
                    'min_qty': min_qty,
                    'current_qty': current_qty
                }
        
        return result

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """Override to validate minimum quantity before adding to cart"""
        product = request.env['product.template'].browse(int(product_id))
        
        # Check if product has minimum quantity enabled
        if product.website_min_qty_enabled:
            min_qty = product.website_min_qty
            requested_qty = int(set_qty) if set_qty else int(add_qty)
            
            if requested_qty < min_qty:
                return request.redirect('/shop/cart?error=min_qty&product=%s&min_qty=%s&current_qty=%s' % (
                    product.name, min_qty, requested_qty
                ))
        
        return super().cart_update(product_id, add_qty, set_qty, **kw)

    @http.route(['/shop/cart'], type='http', auth="public", website=True)
    def cart(self, access_token=None, revive='', **post):
        """Override to handle minimum quantity error messages"""
        response = super().cart(access_token, revive, **post)
        
        # Handle error messages from cart update
        if post.get('error') == 'min_qty':
            product_name = post.get('product', 'Product')
            min_qty = post.get('min_qty', 1)
            current_qty = post.get('current_qty', 0)
            
            response.qcontext['error_message'] = (
                f'Minimum quantity for {product_name} is {min_qty}. '
                f'You tried to add {current_qty} items. Please add at least {min_qty} items.'
            )
        
        return response

    def _get_min_qty_info(self, product_id):
        """Get minimum quantity information for a product"""
        product = request.env['product.template'].browse(product_id)
        if product.website_min_qty_enabled:
            return {
                'enabled': True,
                'min_qty': product.website_min_qty,
                'product_name': product.name
            }
        return {'enabled': False}

    @http.route(['/shop/min_qty_info'], type='json', auth="public", methods=['POST'], website=True)
    def get_min_qty_info(self, product_id):
        """JSON endpoint to get minimum quantity information"""
        return self._get_min_qty_info(product_id)

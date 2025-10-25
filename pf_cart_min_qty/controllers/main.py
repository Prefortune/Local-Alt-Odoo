# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

class WebsiteSaleCartMinQty(WebsiteSale):
    
    def _get_cart_total_quantity(self):
        order = request.website.sale_get_order()
        if not order:
            return 0
        # Exclude delivery products from the total
        total_qty = 0
        for line in order.order_line:
            # Odoo marks delivery lines with is_delivery = True
            if not getattr(line, 'is_delivery', False):
                total_qty += line.product_uom_qty
        return total_qty

    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def shop_checkout(self, **post):
        website = request.env['website'].get_current_website()
        if website.pf_cart_min_qty_enabled:
            min_qty = website.pf_cart_min_qty_value
            total_qty = self._get_cart_total_quantity()
            if total_qty < min_qty:
                return request.render('pf_cart_min_qty.cart_min_qty_warning', {
                    'min_qty': int(min_qty),
                    'total_qty': int(total_qty),
                })
        return super(WebsiteSaleCartMinQty, self).shop_checkout(**post)

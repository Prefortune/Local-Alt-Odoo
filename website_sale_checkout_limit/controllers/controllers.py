# -*- coding: utf-8 -*-
from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo import http
from odoo.http import request, route


class WebsiteSaleExtended(WebsiteSale):
    @http.route()
    def cart_update_json(self, *args, set_qty=None, **kwargs):
        result = super().cart_update_json(*args, set_qty=set_qty, **kwargs)

        is_min = request.website.check_cart_amount()
        result['website_sale.check'] = is_min
        return result

    @route(
        '/shop/checkout', type='http', methods=['GET'], auth='public', website=True, sitemap=False
    )
    def shop_checkout(self, try_skip_step=None, **query_params):
        is_min = request.website.check_cart_amount()
        if is_min:
            return super(WebsiteSaleExtended, self).shop_checkout(try_skip_step=try_skip_step, **query_params)
        return request.redirect("/shop/cart")

    @http.route('/shop/payment', type='http', auth='public', website=True, sitemap=False)
    def shop_payment(self, **post):
        is_min = request.website.check_cart_amount()
        if is_min:
            return super(WebsiteSaleExtended, self).shop_payment(**post)
        return request.redirect("/shop/cart")

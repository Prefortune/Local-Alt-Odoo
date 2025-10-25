from odoo.addons.theme_prime.controllers.main import ThemePrimeWebsiteSale
from odoo.http import request
from odoo import http


class WebsiteSaleTagAndFilter(ThemePrimeWebsiteSale):

    @http.route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        response = super().shop(page=page, category=category, search=search,
                                min_price=min_price, max_price=max_price, ppg=ppg, **post)

        tag_ids = request.httprequest.args.getlist('tags')
        if tag_ids:
            try:
                tag_ids = [int(t) for t in tag_ids]
            except ValueError:
                tag_ids = []

            if tag_ids:
                # סינון לפי כל התגיות (AND)
                products = response.qcontext.get('products')
                if products is not None:
                    for tag_id in tag_ids:
                        products = products.filtered(
                            lambda p: tag_id in p.product_tag_ids.ids)
                    response.qcontext['products'] = products
                    response.qcontext['products_count'] = len(products)

        return response

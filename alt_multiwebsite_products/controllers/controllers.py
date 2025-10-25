from math import log
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import werkzeug
import logging
_logger = logging.getLogger(__name__)

class WebsiteSaleMultiWebsite(WebsiteSale):

    def product(self, product, category='', search='', **kwargs):
        _logger.info("--- from alt WebsiteSaleMultiWebsite(WebsiteSale) is called ---")
        if product._name == 'product.template':
            website_ids = product.website_ids
        else:  # product.product
            website_ids = product.website_ids
            if not website_ids:
                website_ids = product.product_tmpl_id.website_ids

        if website_ids and request.website.id not in website_ids.ids:
            raise werkzeug.exceptions.NotFound()

        return super().product(product=product, category=category, search=search, **kwargs)

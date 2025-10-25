# -*- coding: utf-8 -*-
from math import prod
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import werkzeug
import logging
_logger = logging.getLogger(__name__)

class WebsiteSaleMultiWebsite(WebsiteSale):

    def product(self, product, category='', search='', **kwargs):
        _logger.info("--- WebsiteSaleMultiWebsite Product Is called --- %s",product)
        # אם product הוא טמפלט – זה מה ש־Odoo שולח דרך SEO URL
        if product._name == 'product.template':
            website_ids = product.website_ids
        else:
            website_ids = getattr(product, 'product_tmpl_id', None) and product.product_tmpl_id.website_ids or None

        if website_ids and request.website.id not in website_ids.ids:
            raise werkzeug.exceptions.NotFound()

        return super().product(product=product, category=category, search=search, **kwargs)

import base64
import io
import json
import logging
import re
import string
from collections import defaultdict
import datetime
from odoo.addons.theme_prime.controllers.main import ThemePrimeWebsiteSale
try:
    from werkzeug.utils import send_file
except ImportError:
    from odoo.tools._vendor.send_file import send_file

from odoo import _, http
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist
from odoo.addons.website_sale.controllers.combo_configurator import (WebsiteSaleComboConfiguratorController)
from odoo.http import request
from odoo.osv import expression
from odoo.tools import html_escape, file_path, file_open
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)


class CustomThemePrimeController(ThemePrimeWebsiteSale):
    @http.route('/theme_prime/get_quick_view_html', type='json', auth='public', website=True)
    def get_quick_view_html(self, options, **kwargs):
        IrUiView = request.env['ir.ui.view']
        product_tmpl_id = options.get('product_tmpl_id')
        product_id = options.get('product_id')
        extra = {}
        if product_id:
            product_variant = request.env['product.product'].browse(product_id)
            product_tmpl_id = product_variant.product_tmpl_id.id
            extra = {'dr_variant_id': product_variant}
        domain = expression.AND([request.website.sale_product_domain(), [('id', '=', product_tmpl_id)]])
        product = request.env['product.template'].search(domain, limit=1)

        # If moved to another website or delete
        if not product:
            return False

        values = self._prepare_product_values(product, category='', search='', **kwargs)
        result = request.website.get_theme_prime_shop_config()
        values.update(result)
        values.update(extra)

        if options.get('variant_selector'):

            current_site = request.website
            most_expensive_variant = False

            price_list = request.env['product.pricelist'].search([('website_id','=',current_site.id)])
            if price_list:
                # _logger.info("--- price_list --- %s",price_list.name)
                # _logger.info("--- product.product_variant_ids --- %s",product.product_variant_ids)
                variant_price_items = price_list.item_ids.filtered(lambda i: i.product_id in product.product_variant_ids)
                if variant_price_items:
                    most_expensive_item = max(variant_price_items, key=lambda i: i.fixed_price, default=False)
                    most_expensive_variant = most_expensive_item.product_id if most_expensive_item else False
                else:
                    most_expensive_variant = product.product_variant_ids.sorted(key=lambda v: v.lst_price, reverse=True)[:1]
            else:
                most_expensive_variant = product.product_variant_ids.sorted(key=lambda v: v.lst_price, reverse=True)[:1]

            if most_expensive_variant:
                values['dr_variant_id'] = most_expensive_variant
            values['auto_add_product'] = product.product_variant_count == 1
            return IrUiView._render_template('theme_prime.product_variant_selector_dialog', values=values)

        if options.get('right_panel'):
            return IrUiView._render_template('theme_prime.tp_product_right_panel', values=values)
        
        return IrUiView._render_template('theme_prime.tp_product_quick_view', values=values)
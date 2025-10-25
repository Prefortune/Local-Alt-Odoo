from email.policy import default
from odoo import models, fields
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    website_price_range = fields.Char(compute='_compute_website_price_range', store=False)

    def _compute_website_price_range(self):
        website = self.env['website'].get_current_website()
        price_list = self.env['product.pricelist'].search([('website_id', '=', website.id)], limit=1)

        for template in self:
            if price_list:
                # Compute prices using pricelist method for accuracy
                prices = [price_list._get_product_price(variant, 1.0) for variant in template.product_variant_ids]
            else:
                prices = template.product_variant_ids.mapped('lst_price')

            if prices:
                min_price, max_price = min(prices), max(prices)
                template.website_price_range = f"{min_price:.2f}" if min_price == max_price else f"{min_price:.2f} - {max_price:.2f}"


class WebSite(models.Model):
    _inherit = 'website'

    is_price_range = fields.Boolean(string="Want To Show Price Range In Shop Page", default=False)

    

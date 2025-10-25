from venv import logger
from odoo import api, fields, models
from odoo.addons.http_routing.models.ir_http import slug
from werkzeug.urls import url_join


import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    product_slug = fields.Char(string="product Slug")

    def _compute_product_website_url(self):
         super()._compute_product_website_url()
         for product in self:
            if product.product_slug:
                attributes = ','.join(str(x) for x in product.product_template_attribute_value_ids.ids)
                print('attribtues...............................',attributes)
                if attributes:
                    url = url_join(url, f"#attr={attributes}")

                url = product.product_tmpl_id.website_url
                print('url.......................',url)
                
                product_slug = product.product_slug or ''  
                
                url = f"{url}/{product_slug}"
                product.website_url = url
            return product.website_url



class ProductCombo(models.Model):
    _inherit = "pos.combo"

    @api.depends("combo_line_ids")
    def _compute_base_price(self):
        for rec in self:
            # Use the lowest price of the combo lines as the base price
            rec.base_price = sum(rec.combo_line_ids.mapped("product_id.lst_price")) if rec.combo_line_ids else 0

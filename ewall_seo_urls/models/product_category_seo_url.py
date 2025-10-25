# -*- coding: utf-8 -*-
from odoo import fields, models

# Product Template Added SEO URL Field
class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "website_seo_url"]

    seo_url_language = fields.Selection(
        [('english', 'English'), ('arabic', 'Arabic'), ('hebrew', 'Hebrew')],
        string='URL Language',
        default='english',
        required=True,
        help='Select the language for the URL validation.',
    )

    seo_url = fields.Char("Product URL", help='URL field that supports only the selected language (English or Arabic).', index=True)

    def _compute_website_url(self):
        res = super(ProductTemplate, self)._compute_website_url()
        for product in self:
            if product.seo_url:
                product.website_url = "/shop/%s" % (product.seo_url)
            elif product.id:
                product.website_url = "/shop/%s" % self.env['ir.http']._slug(product)
        return res


# Category Added SEO URL Field
class ProductPublicCategory(models.Model):
    _name = "product.public.category"
    _inherit = ["product.public.category", "website_seo_url"]

    seo_url_language = fields.Selection(
        [('english', 'English'), ('arabic', 'Arabic'), ('hebrew', 'Hebrew')],
        string='URL Language',
        default='english',
        required=True,
        help='Select the language for the URL validation.',
    )

    seo_url = fields.Char("Category URL", help='URL field that supports only the selected language (English or Arabic).', index=True)

# Product Hover Product ID Remove Functionality 
class ProductProductInherit(models.Model):
    _inherit = "product.product"

    def _compute_product_website_url(self):
        res = super(ProductProductInherit, self)._compute_product_website_url()
        for product in self:
            url = product.product_tmpl_id.website_url
            if pavs := product.product_template_attribute_value_ids.product_attribute_value_id:
                pav_ids = [str(pav.id) for pav in pavs]
                if pav_ids:
                    url = f'{url}#attribute_values={",".join(pav_ids)}'
                else:
                    url = product.product_tmpl_id.website_url
            product.website_url = url
        return res
from odoo import models, fields

# class ProductTemplate(models.Model):
#     _inherit = "product.template"

#     website_ids = fields.Many2many(
#         "website",
#         "product_template_website_rel",
#         "product_tmpl_id",
#         "website_id",
#         string="Websites (Templates)"
#     )

class Product(models.Model):
    _inherit = "product.product"

    website_ids = fields.Many2many(
        "website",
        "product_product_website_rel",
        "product_id",
        "website_id",
        string="Websites (Variants)"
    )

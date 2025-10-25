from odoo import models, fields, api

class WebsiteProductCTASettings(models.TransientModel):
    _name = 'website.product.cta.settings'
    _description = 'Product CTA Button Settings'

    cta_behavior = fields.Selection([
        ('default', 'Add to cart only'),
        ('contact_only', 'Contact us only'),
        ('both', 'Add to cart and Contact us'),
    ], string="CTA Behavior", default='default')

    cta_link = fields.Char(string="Contact Us URL")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        config = self.env['ir.config_parameter'].sudo()
        res['cta_behavior'] = config.get_param('alt_product_cta_button.cta_behavior', 'default')
        res['cta_link'] = config.get_param('alt_product_cta_button.cta_link', '')
        return res

    def save_settings(self):
        config = self.env['ir.config_parameter'].sudo()
        config.set_param('alt_product_cta_button.cta_behavior', self.cta_behavior)
        config.set_param('alt_product_cta_button.cta_link', self.cta_link)

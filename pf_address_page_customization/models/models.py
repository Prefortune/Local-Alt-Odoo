# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    size = fields.Char(string="Size")
    kosher = fields.Char(string="Kosher")


class Website(models.Model):
    _inherit = 'website'

    pf_website_product_label = fields.Boolean(string="Website Product Label")

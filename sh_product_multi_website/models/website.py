# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models
import logging
_logger = logging.getLogger(__name__)

class Website(models.Model):
    _inherit = "website"

    def sale_product_domain(self):
        _logger.info("--- sale_product_domain is called ---")
        return [("sale_ok", "=", True)] + [
            "|",
            ("website_ids", "=", False),
            ("website_ids", "in", self.get_current_website().ids)]

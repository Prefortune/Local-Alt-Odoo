# Copyright © 2022 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License OPL-1 (https://www.odoo.com/documentation/14.0/legal/licenses.html).

from odoo import api, fields, models
from .product_product import FB_STATUSES


class ProductTemplate(models.Model):
    _inherit = "product.template"

    feed_fb_status = fields.Selection(
        selection=FB_STATUSES,
        string='Status',
        compute='_compute_feed_fb_status',
        inverse='_inverse_feed_fb_status',
        store=True,
    )

    @api.depends('product_variant_ids.feed_fb_status')
    def _compute_feed_fb_status(self):
        self._compute_template_field_from_variant_field('feed_fb_status')

    def _inverse_feed_fb_status(self):
        self._set_product_variant_field('feed_fb_status')

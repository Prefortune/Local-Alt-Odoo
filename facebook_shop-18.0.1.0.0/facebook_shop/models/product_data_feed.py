from odoo import fields, models


class ProductDataFeed(models.Model):
    _inherit = "product.data.feed"

    recipient_is_facebook_shop = fields.Boolean(compute='_compute_recipient_is_facebook_shop')

    def _compute_recipient_is_facebook_shop(self):
        for feed in self:
            feed.recipient_is_facebook_shop = feed.recipient_id == self.env.ref('facebook_shop.recipient_facebook')

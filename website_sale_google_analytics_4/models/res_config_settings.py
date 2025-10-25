# Copyright © 2021 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gtag_serving_url = fields.Char(
        related='website_id.gtag_serving_url',
        readonly=False,
        string="Tag Serving URL",
    )

    def action_restore_google_tag_serving_url(self):
        if self.website_id:
            self.gtag_serving_url = "https://www.googletagmanager.com/"

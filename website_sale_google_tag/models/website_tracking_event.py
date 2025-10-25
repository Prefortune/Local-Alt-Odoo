# Copyright © 2024 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html)

from odoo import api, models


class WebsiteTrackingEvent(models.Model):
    _inherit = "website.tracking.event"

    @api.model
    def google_tag_send_to(self):
        return super(WebsiteTrackingEvent, self).google_tag_send_to() + ['gtm']

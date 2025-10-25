# Copyright © 2024 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html)

from typing import List

from odoo import api, fields, models


class WebsiteTrackingEvent(models.Model):
    _inherit = "website.tracking.event"

    send_to = fields.Char(string='Destination (send to)')  # 'send_to' can be a list: ['G-XXXXXX-1', 'AW-YYYYYY']

    @api.model
    def google_tag_send_to(self) -> List[str]:
        return []

    @api.model_create_multi
    def create(self, vals_list):
        records = super(WebsiteTrackingEvent, self).create(vals_list)
        for event in records:
            if event.service_type in self.google_tag_send_to() and not event.send_to:
                event.write({'send_to': event.service_id.key})
        return records

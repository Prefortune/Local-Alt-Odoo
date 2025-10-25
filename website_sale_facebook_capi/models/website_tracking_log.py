# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

import json
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class WebsiteTrackingLog(models.Model):
    _inherit = "website.tracking.log"

    channel = fields.Selection(
        selection_add=[('fb_capi', 'Facebook CAPI')],
        ondelete={'fb_capi': 'cascade'},
    )
    fbp = fields.Char(string="Facebook browser ID", readonly=True)
    fbc = fields.Char(string="Facebook click ID", readonly=True)

    def fb_capi_get_event_data(self):
        datas = []
        for log in self:
            payload = json.loads(log.payload)
            payload_data = payload['data']
            data = {
                "event_name": payload.get('event_name'),
                "event_id": str(log.id),
                "event_time": self._to_unix_time(log.create_date),
                "action_source": "website",
                "event_source_url": log.url or '',
                "user_data": {},
                "custom_data": payload_data,
            }

            user_data = data['user_data']
            user_data["fbp"] = log.fbp
            user_data["fbc"] = log.fbc
            user_data.update(
                log.service_id.with_context(data_from_request=False).get_visitor_data(
                    visitor_id=log.visitor_id.id, sale_order_id=log.order_id.id, log_id=log.id,
                )
            )

            # Update payload
            payload['user_data'].update(user_data)
            log.sudo().write({'payload': json.dumps(payload)})

            datas.append(data)
            if log.website_id.tracking_is_logged:
                _logger.debug("[FB CAPI] Request Data: %s", data)

        return datas

    def action_send_event(self):
        self.ensure_one()
        if self.service_id.is_fb_capi():
            self.service_id.fb_capi_send_request(self)
        return super(WebsiteTrackingLog, self).action_send_event()

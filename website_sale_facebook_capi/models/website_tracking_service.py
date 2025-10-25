# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

import json
import logging
from datetime import timedelta
import requests

from odoo import api, fields, models
from odoo.http import request
from .website_tracking_log import WebsiteTrackingLog

_logger = logging.getLogger(__name__)


class WebsiteTrackingService(models.Model):
    _inherit = "website.tracking.service"

    def is_fb_capi(self):
        self.ensure_one()
        return self.type == 'fbp' and self.api_is_active

    @api.depends('type')
    def _compute_api_is_available(self):
        res = super(WebsiteTrackingService, self)._compute_api_is_available()
        for service in self:
            if service.type == 'fbp':
                service.api_is_available = True
        return res

    def extra_log_data(self):
        self.ensure_one()
        res = super(WebsiteTrackingService, self).extra_log_data()
        if self.is_fb_capi():
            res.update({
                'channel': 'fb_capi',
                'state': 'to_send',
                'fbp': request and request.httprequest.cookies.get('_fbp', ''),
                'fbc': request and request.httprequest.cookies.get('_fbc', ''),
            })
        return res

    def fb_capi_send_request(self, logs: WebsiteTrackingLog):
        self.ensure_one()
        service = self
        response = None

        request_data = {'data': logs.fb_capi_get_event_data()}
        if not request_data['data']:
            return response

        if service.api_test_code:
            request_data.update({'test_event_code': service.api_test_code})

        log_vals = {'api_sent_date': fields.Datetime.now()}
        try:
            response = requests.post(
                url=f'https://graph.facebook.com/v16.0/{service.key}/events',
                json=request_data,
                params={'access_token': service.api_token},
                timeout=120,
            )

            if service.website_id.tracking_is_logged:
                _logger.debug("[FB CAPI] Response: %s | %s | %s", response.status_code, response.json(), response.text)

            # If tracking data lacks a customer data, mark this event as warning
            error = response.json().get('error', {})
            if response.status_code == 400 and error.get('code') == 100 and error.get('error_subcode') == 2804050:
                log_vals.update({
                    'state': 'warning',
                    'api_response': f"{error.get('error_user_title', '')}\n"
                                    f"{error.get('error_user_msg', '')}\n"
                                    f"fbtrace_id: {error.get('fbtrace_id', '')}",
                })
            else:
                response.raise_for_status()
                log_vals.update({'state': 'sent'})

        except requests.HTTPError as e:
            _logger.error(
                "[FB CAPI] HTTP Error: %r, msg: %r, content: %r)",
                e.response.status_code, e.response.reason, response.json(),
            )
            log_vals.update({
                'state': 'error',
                'api_response': "%s | Reason: %s | %s" % (
                    e.response.status_code, e.response.reason, json.dumps(response.json())
                ),
                # response.text.decode(response.encoding)
            })
        except Exception as e:
            _logger.error("[FB CAPI] Other Error: %s", str(e))
            log_vals.update({'state': 'error', 'api_response': str(e)})
        else:
            if response.status_code != requests.codes.ok and log_vals.get('state') != 'warning':
                _logger.error(
                    "[FB CAPI] Request Error: %r, msg: %r, content: %r)",
                    response.status_code, response.reason, response.json(),
                )
                log_vals.update({
                    'state': 'error',
                    'api_response': "%s | %s" % (response.status_code, json.dumps(response.json())),
                })

        finally:
            logs.sudo().write(log_vals)

        return response

    @api.model
    def _fb_capi_send_events(self):
        """Method to make batch request by the cron."""
        services = self.search([
            ('type', '=', 'fbp'),
            ('api_is_active', '=', True),
        ])
        for service in services:
            logs = self.env['website.tracking.log'].search([
                ('service_id', '=', service.id),
                ('channel', '=', 'fb_capi'),
                ('state', '=', 'to_send'),
                ('api_send_is_denied', '=', False),
                # The "event_time" can be up to 7 days before you send an event to Meta
                ('create_date', '>', fields.Datetime.now() - timedelta(days=7)),
            ])
            service.fb_capi_send_request(logs)

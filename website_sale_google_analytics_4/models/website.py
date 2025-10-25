# Copyright © 2023 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License OPL-1 (https://www.odoo.com/documentation/14.0/legal/licenses.html).

from typing import Dict, List

from odoo import api, models, fields
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    gtag_serving_url = fields.Char(default='https://www.googletagmanager.com/')

    @api.model
    def _tracking_event_mapping(self, service_type):
        res = super(Website, self)._tracking_event_mapping(service_type)
        if service_type in self.env['website.tracking.service']._get_google_types():
            res = {
                'lead': 'generate_lead',
                'login': 'login',
                'sign_up': 'sign_up',
                'view_product': 'view_item',
                'view_product_list': 'view_item_list',
                'search_product': 'search',
                'add_to_wishlist': 'add_to_wishlist',
                'add_to_cart': 'add_to_cart',
                'begin_checkout': 'begin_checkout',
                'add_shipping_info': 'add_shipping_info',
                'add_payment_info': 'add_payment_info',
                'purchase': 'purchase',
                'purchase_portal': 'purchase',
            }
        return res

    def _gtag_params(self):
        # flake8: noqa: E501
        """The method is completely overridden to get params related to tracking services."""
        super(Website, self)._gtag_params()
        params = {}
        service = self.env['website.tracking.service'].sudo().browse(self._context.get('tracking_service_id'))
        if service:
            if service.type == 'ga4' and service.ga4_debug_mode:
                params.update({'debug_mode': True})
            if service.track_id_external and request and request.env.user.has_group('base.group_portal') and request.env.user.ga4_ref:
                # Send "User-ID" only for portal users
                params.update({'user_id': request.env.user.ga4_ref})
            if service.type == 'gtag' and service.gtag_enhanced_conversions:
                params.update({'allow_enhanced_conversions': True})
        return params

    def _gtag_configs(self):
        super(Website, self)._gtag_configs()
        configs = []
        for service in self.sudo().tracking_service_ids.filtered(
                lambda sv: sv.type in self.env['website.tracking.service']._get_gtag_types() and sv.active
        ):
            configs.append({
                'key': service.key,
                'params': self.with_context(tracking_service_id=service.id)._gtag_params(),
            })
        return configs

    def gtag_get_primary_key(self):
        super(Website, self).gtag_get_primary_key()
        primary_service = self.sudo().tracking_service_ids.filtered(
            lambda sv: sv.type in self.env['website.tracking.service']._get_gtag_types() and sv.active
        )
        return primary_service and primary_service[0].key or ''

    def _tracking_do_logging(self, service) -> bool:
        """ The Internal Logging can be used internally in a company for analytics or marketing purposes, so
            this logic prevents to make internal logging if no one of these consents is granted.
        """
        self.ensure_one()
        do_logging = super(Website, self)._tracking_do_logging(service)
        if service.type not in self.env['website.tracking.service']._get_google_types():
            return do_logging
        return do_logging and (self._cookies_analytics_is_granted() or self._cookies_marketing_is_granted())

    def _gtag_extra_calls(self) -> List[Dict]:
        """ Prepare a customer data for the enhanced conversions. """
        self.ensure_one()
        services = self.sudo().tracking_service_ids.filtered(
            lambda s: s.type in ['gtag', 'gtm'] and s.active and s.gtag_enhanced_conversions
        )
        if not services:
            return []

        # Unite data for services, as all Google services use a single gtag calling "user_data",
        # in case when hashed and not hashed values are in the different Google services.
        user_data = {}
        for service in services:
            # Group the address data
            user_data.update(service.get_visitor_data())

        return [{
            'action': 'set',
            'param_name': 'user_data',
            'param_vals': services[0].complete_user_data(user_data),
        }]

    def gtag_get_source_url(self):
        """
        Rewrite method completely to add the custom serving URL.
        """
        # super(Website, self).gtag_get_source_url()
        return f"{self.gtag_serving_url.rstrip('/')}/gtag/js?id={self.gtag_get_primary_key()}"

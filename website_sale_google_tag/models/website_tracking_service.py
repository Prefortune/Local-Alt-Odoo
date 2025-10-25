# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WebsiteTrackingService(models.Model):
    _inherit = "website.tracking.service"

    type = fields.Selection(
        selection_add=[('gtm', 'Google Tag Manager')],
        ondelete={'gtm': 'cascade'},
    )

    @api.constrains('type', 'website_id', 'active')
    def _check_gtm_unique(self):
        for service in self:
            if self.search_count([
                    ('type', '=', 'gtm'),
                    ('website_id', '=', service.website_id.id),
                    ('active', '=', True),
            ]) > 1:
                raise ValidationError(_('The active GTM container must be a single per website.'))

    def get_custom_event_data(self, custom_event, product_data_list=None, order=None, pricelist=None):
        self.ensure_one()
        if self.type != 'gtm':
            return super(WebsiteTrackingService, self).get_custom_event_data(
                custom_event=custom_event,
                product_data_list=product_data_list,
                pricelist=pricelist,
                order=order,
            )
        data = {}
        if custom_event.send_to:
            data['send_to'] = custom_event.send_to
        return data

    @api.model
    def _get_google_types(self):
        return super(WebsiteTrackingService, self)._get_google_types() + ['gtm']

    @api.model
    def _get_privacy_url(self):
        urls = super(WebsiteTrackingService, self)._get_privacy_url()
        urls.update({'gtm': 'https://support.google.com/tagmanager/answer/9323295'})
        return urls

    @api.model
    def _with_custom_events_allowed(self):
        """ A list of tracking service types that are allowed to use custom events. """
        return super(WebsiteTrackingService, self)._with_custom_events_allowed() + ['gtm']

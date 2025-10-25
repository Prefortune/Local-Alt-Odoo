# Copyright © 2024 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

from typing import Any, Dict, List

from odoo import api, fields, models


class WebsiteGoogleConsent(models.Model):
    _name = "website.google.consent"
    _description = 'Google Consent Mode Settings'

    website_id = fields.Many2one(
        comodel_name='website',
        ondelete='cascade',
        required=True,
    )
    # Google Consent parameters are implemented as Boolean fields,
    # we assume that their True value equals to the "granted" value, and False - to the "denied"
    ad_storage = fields.Boolean(default=False)
    ad_user_data = fields.Boolean(default=False)
    ad_personalization = fields.Boolean(default=False)
    analytics_storage = fields.Boolean(default=False)
    functionality_storage = fields.Boolean(default=False)
    personalization_storage = fields.Boolean(default=False)
    security_storage = fields.Boolean(default=True)

    region_ids = fields.Many2many(comodel_name='website.google.consent.region', string='Regions')
    wait_for_update = fields.Integer(
        string='Wait for Update',
        default=0,
        help='Specify how many milliseconds to wait for the consent "update" calling by your CMP.',
    )
    active = fields.Boolean(default=True)

    @api.depends('website_id', 'region_ids.country_id', 'region_ids.state_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s (%s)" % (rec.website_id.name, ', '.join(rgn.display_name for rgn in rec.region_ids))

    def _get_params(self) -> Dict[str, Any]:
        self.ensure_one()
        param_list = [
            'ad_storage', 'ad_user_data', 'ad_personalization', 'analytics_storage',
            'functionality_storage', 'personalization_storage', 'security_storage',
        ]
        params: Dict[str, Any]
        params = {param: 'granted' if self[param] else 'denied' for param in param_list}

        # Additional settings
        if self.wait_for_update:
            params['wait_for_update'] = self.wait_for_update
        if self.region_ids:
            params['region'] = [rgn.display_name for rgn in self.region_ids]

        return params

    def write(self, vals):
        """ Invalidate the caches to apply changes on webpages. """
        result = super(WebsiteGoogleConsent, self).write(vals)
        self.env.registry.clear_cache()
        return result

    @api.model
    def cookie_consent_mapping(self) -> Dict[str, List[str]]:
        """ Return a structure of Odoo's cookie type with related google consent types.
            The standard Odoo cookies types: "required", "optional".
            The additional - custom Odoo cookies types, which replace and extend the standard "optional" type:
            "functional", "analytics", "marketing".
        """
        return {
            # Standard Odoo cookie consents
            'required': ['security_storage'],
            'optional': [
                'functionality_storage', 'personalization_storage', 'analytics_storage',
                'ad_personalization', 'ad_storage', 'ad_user_data',
            ],
            # Custom Odoo cookie consents
            'functional': ['functionality_storage', 'personalization_storage'],
            'analytics': ['analytics_storage'],
            'marketing': ['ad_personalization', 'ad_storage', 'ad_user_data'],
        }

    @api.model
    def get_consent_by_cookie_type(self, cookie_type: str = None) -> List[str]:
        return self.cookie_consent_mapping().get(cookie_type, [])

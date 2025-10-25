# Copyright © 2024 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

from typing import Dict

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    google_consent_mode_ids = fields.One2many(
        comodel_name='website.google.consent',
        inverse_name='website_id',
        string='Google Consent Modes',
    )
    # Additional Google Consent settings
    google_consent_ads_data_redaction = fields.Boolean(string='Ads Data Redaction')
    google_consent_url_passthrough = fields.Boolean(string='URL Passthrough')

    def _get_google_consents(self) -> Dict[str, str]:
        """ Return a dictionary with a website visitor cookie consents.
            Note: To use with the CMP - Odoo Cookie Bar.
        """
        self.ensure_one()
        params = {}
        for cookie_type, is_granted in self._get_cookie_consents().items():
            consents = self.env['website.google.consent'].get_consent_by_cookie_type(cookie_type)
            for consent in consents:
                params[consent] = 'granted' if is_granted else 'denied'
        return params

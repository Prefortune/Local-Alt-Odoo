from typing import Dict

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website


class WebsiteConsentCookiesBar(Website):

    @http.route(['/website/cookies/google_consents'], type='json', auth="public", website=True)
    def get_google_cookies_consents(self) -> Dict[str, str]:
        website = request.website
        if website.cookies_consent_manager == 'odoo' and website._get_cookie_consents():
            return website._get_google_consents()
        return {}

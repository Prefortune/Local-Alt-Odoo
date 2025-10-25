/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import CookiesConsentWidget from '@website_cookies_consent/js/cookies_consent';
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.cookies_bar_google_consent = CookiesConsentWidget.extend({
    selector: '#website_cookies_bar',
    events: { 'click #cookies-consent-essential, #cookies-consent-all': '_updateCookieConsent' },

    init() {
        this._super(...arguments);
        this.rpc = rpc;
    },

    /**
    * @override
    */
    async _updateCookieConsent() {
        this._super.apply(this, arguments);
        let self = this;
        const cookieManager = this._getCookieConsentManager();
        if ( cookieManager === 'odoo' ) {
            const websiteGtag = window.gtag || function () {};
            // Pause to allow updating cookies by Odoo
            await new Promise(resolve => setTimeout(resolve, 2000));
            this.rpc(
                '/website/cookies/google_consents'
            ).then(function (paramConsents) {
                if (self._isCookieConsentLogged()) {
                    console.log(`[Cookie Consent | Google] _updateCookieConsent: ${JSON.stringify(paramConsents)}`);
                }
                websiteGtag.call(this, 'consent', 'update', paramConsents);
            }).catch(error => console.log(error))
        }
        // return this._super.apply(this, arguments);
    },
});

export default publicWidget.registry.cookies_bar_google_consent;

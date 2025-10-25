/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import CookiesConsentWidget from '@website_cookies_consent/js/cookies_consent';

publicWidget.registry.cookies_bar_facebook_consent = CookiesConsentWidget.extend({
    selector: '#website_cookies_bar',
    events: {
        'click #cookies-consent-essential, #cookie-banner-essential': '_onAcceptRequiredCookies',
        'click #cookies-consent-all, #cookie-banner-all': '_onAcceptOptionalCookies',
    },

    /**
    * @private
    * @param {Event} ev
    */
    _onAcceptRequiredCookies(ev) {
        // Click on Essential Cookies Only
        if (ev.target.id === 'cookies-consent-essential' || ev.target.id === 'cookie-banner-essential') {
            if (this._isCookieConsentLogged()) { console.log(`[Cookie Consent | Facebook] - Revoke`) }
            const websiteFbq = window.fbq || function () {};
            websiteFbq.call(this, 'consent', 'revoke');
        }
    },
    /**
    * @private
    * @param {Event} ev
    */
    _onAcceptOptionalCookies(ev) {
        // Click on All Cookies
        if (ev.target.id === 'cookies-consent-all' || ev.target.id === 'cookie-banner-all') {
            if (this._isCookieConsentLogged()) { console.log(`[Cookie Consent | Facebook] - Grant`) }
            const websiteFbq = window.fbq || function () {};
            websiteFbq.call(this, 'consent', 'grant');
        }
    },
    /**
    * @override
    */
    async _updateCookieConsent() {
        this._super.apply(this, arguments);
        if (self._isCookieConsentLogged()) {
            console.log(`[Cookie Consent | Facebook] _updateCookieConsent`);
        }
    },
});

export default publicWidget.registry.cookies_bar_facebook_consent;

/** @odoo-module **/

import paymentForm from '@payment/js/payment_form';
import { _t } from "@web/core/l10n/translation";

paymentForm.include({

    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'payplus') {
            return this._super(...arguments);
        }
        this._setPaymentFlow('direct');
    },

    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'payplus') {
            return this._super(...arguments);
        }

        // You can log for debugging
        console.log("PayPlus processingValues:", processingValues);

        const redirectUrl = processingValues['redirect_url'];

        if (redirectUrl) {
            // Redirect user to PayPlus form
            window.location.href = redirectUrl;
        } else {
            this._displayErrorDialog(
                _t("Missing Payment Information"),
                _t("PayPlus did not return a redirect URL.")
            );
        }
    },

});

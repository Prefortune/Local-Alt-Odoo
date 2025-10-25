/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.websiteTrackingAlternative = publicWidget.registry.websiteSaleTrackingAlternative.extend({
    // TODO: need change binding object
    selector: 'i.fa.fa-paper-plane.fa-2x.mb-3.rounded-circle.text-bg-success',

    start: function (ev) {
        this.trigger_up('tracking_lead');
        return this._super.apply(this, arguments);
    },
});

export default publicWidget.registry.websiteTrackingAlternative;

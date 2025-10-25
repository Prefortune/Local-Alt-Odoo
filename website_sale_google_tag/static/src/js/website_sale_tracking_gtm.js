/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.websiteSaleTrackingAlternative.include({

    trackingSendEventData: function(eventType, eventData) {
        if (this.trackingIsLogged()) { console.log('-- GTM Tracking is running --') }
        if (eventData['gtm'] !== undefined && Array.isArray(eventData['gtm'])) {
            for(let i = 0; i < eventData['gtm'].length; i++) {
                if (this.trackingIsLogged()) { console.log(eventData['gtm'][i]) }
                let run_script = eventData['gtm'][i]['run_script']
                let event_name = eventData['gtm'][i]['event_name']
                let event_data = eventData['gtm'][i]['data']
                if (event_data !== undefined && run_script !== undefined && run_script) {
                    let _data_Layer = window.dataLayer || [];
                    if (this.trackingIsLogged()) { console.log("-- GTM Tracking push() --") }
                    _data_Layer.push({'ecommerce': null});  // Clear the previous ecommerce object
                    _data_Layer.push({'event': event_name, 'ecommerce': event_data});
                }
            }
        }
        return this._super.apply(this, arguments);
    },
})

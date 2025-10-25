/** @odoo-module **/

import websiteSaleTracking from "@website_sale/js/website_sale_tracking";

websiteSaleTracking.include({
    /**
     * Skip default GA tracking.
     * @override
    */
    _trackGA: function () {}
})

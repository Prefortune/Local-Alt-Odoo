/** @odoo-module **/
import { WebsiteSale } from "@website_sale/js/website_sale";
import WebsiteSaleTrackingAlternative from "@website_sale_tracking_base/js/website_sale_tracking";


WebsiteSale.include({
    /**
     * @private
     * @override
     * @param {Event} ev
     */
    _onChangeCartQuantity: async function (ev) {
        const _super = this._super.bind(this);
        let $input = $(ev.currentTarget);
        let value = parseInt($input.val() || 0, 10);
        if (isNaN(value)) {
            value = 1;
        }
        let websiteSaleTracking = new WebsiteSaleTrackingAlternative(this);
        if (value) {
            websiteSaleTracking.trackingExecuteEvent({
                event_type: 'update_cart',
                item_type: 'product.product',
                product_ids: [$input.data('productId'),],
                product_qty: value,
            });
        } else {
            // In this case window.location can be changed from promise resolve inside super method
            // to avoid situations when the tracked data does not have time to be sent,
            // we need to wait for it to be sent
            await websiteSaleTracking.trackingExecuteEvent({
                event_type: 'remove_from_cart',
                item_type: 'product.product',
                product_ids: [$input.data('productId'),],
                product_qty: 0,
            });
            // wait a second if browser is Mozilla Firefox
            // because if window.location is changed Firefox will drop tracking request
            if (navigator.userAgent.includes("Firefox")) {
                const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay));
                await sleep(1000);
            }
        }
        return _super(...arguments);
    },
});

export default WebsiteSale;

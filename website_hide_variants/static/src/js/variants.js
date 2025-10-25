/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

// Define the widget
publicWidget.registry.HideVarients = publicWidget.Widget.extend({
    selector: '#product_detail',

    start: function () {
        console.log('🚀 ✅ Start HideVarients widget registered!');
        this._hideVariants();
        return this._super.apply(this, arguments);
    },

    _hideVariants: function () {
        const self = this;

        // Find the currently selected product variant ID from the hidden input
        let productId = parseInt(this.$el.find('input.product_id').val());

        console.log("🔍 Selected product ID:", productId);

        if (!isNaN(productId) && productId) {
            rpc('/variants/' + productId, {}).then(function(res) {
                if (res) {
                    console.log(`🚫 Hiding variant with ID ${productId}`);
                    // Hide the entire section if the variant should be hidden
                    self.$el.find('input.product_id').closest('div.js_product').remove();
                }
            }).catch(function(error) {
                console.error('❌ RPC error for variant ID', productId, error);
            });
        }
    },
});

export default publicWidget.registry.HideVarients;

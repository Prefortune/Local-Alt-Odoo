/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

console.log('📦 Alt Split Delivery JS module loaded!');

publicWidget.registry.AltSplitDeliveryCheckout = publicWidget.Widget.extend({
    selector: '#shop_checkout',

    // console.log('🛒 AltSplitDeliveryCheckout widget initialized!')
    events: {
        'click .o_alt_split_delivery_plus': '_onPlus',
        'click .o_alt_split_delivery_minus': '_onMinus',
        'change .o_alt_split_delivery_qty': '_onInputChange',
    },

    start: function () {
        console.log('🚀 AltSplitDeliveryCheckout widget STARTED!', this);
        return this._super.apply(this, arguments);
    },

    _getSelectedDeliveryMethod() {
    const $selected = this.$('input[name="o_delivery_radio"]:checked');
    if ($selected.length) {
        const dmId = $selected.data('dm-id');
        const supportsSplit = $selected.data('is-supports-split');  // or 'data-supports-split'
        const deliveryType = $selected.data('delivery-type');
        console.log('📦 Selected Delivery Method:', {
            dmId,
            supportsSplit,
            deliveryType
        });
        return {
            dmId,
            supportsSplit,
            deliveryType,
            $el: $selected
        };
    } else {
        console.warn('⚠️ No delivery method selected.');
        return null;
    }
},


    _onPlus: function (ev) {
        const selected = this._getSelectedDeliveryMethod();
        console.log('🔼 Plus clicked for delivery method:', selected);

        const $input = this.$('.o_alt_split_delivery_qty');
        let qty = parseInt($input.val()) || 1;
        qty++;
        $input.val(qty);
        
        console.log('➕ Plus clicked → Qty:', qty);
    },

    _onMinus: function (ev) {
        const selected = this._getSelectedDeliveryMethod();
        console.log('🔽 Minus clicked for delivery method:', selected);
        const $input = this.$('.o_alt_split_delivery_qty');
        let qty = parseInt($input.val()) || 1;
        if (qty > 1) {
            qty--;
            $input.val(qty);
            console.log('➖ Minus clicked → Qty:', qty);
        }
    },

    _onInputChange: function (ev) {
        const val = parseInt($(ev.currentTarget).val()) || 1;
        console.log('🔁 Qty changed manually:', val);
    }
});

console.log('✅ Alt Split Delivery widget registered!');
return publicWidget.registry.AltSplitDeliveryCheckout;

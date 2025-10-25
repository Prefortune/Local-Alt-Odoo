/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from '@web/core/network/rpc';

publicWidget.registry.WebsiteSaleCheckout.include({

    events: {
        ...publicWidget.registry.WebsiteSaleCheckout.prototype.events,
        'change #toggle_delivery_date': '_onToggleCheckbox',
        'change .set_delivery_date': '_onInputChange',
        'click #delivery_date': '_onClickDeliveryDate',
    },

    async start() {
        console.log('📦 WebsiteSaleCheckout extended for delivery date with checkbox!');
        return this._super.apply(this, arguments);
    },

    _onToggleCheckbox: function (ev) {
        const checked = $(ev.currentTarget).is(':checked');
        const $input = $('#delivery_date');
        const $errorDiv = $('#delivery_date_error');

        if (checked) {
            $input.show().attr('required', true);
        } else {
            $input.hide().val('').removeAttr('required');
            $errorDiv.hide().text('');
        }
    },

    _getOrderDateValue() {
        return $('#delivery_date').val();
    },

    _onInputChange: function (ev) {
        const deliveryDate = this._getOrderDateValue();
        const $errorDiv = $('#delivery_date_error');
        const checkboxChecked = $('#toggle_delivery_date').is(':checked');

        $errorDiv.hide().text('');

        if (!checkboxChecked) return; // Ignore if checkbox is not checked

        if (!deliveryDate) return;

        const selectedDate = new Date(deliveryDate);
        const today = new Date();
        selectedDate.setHours(0, 0, 0, 0);
        today.setHours(0, 0, 0, 0);

        if (selectedDate < today) {
            $errorDiv.text("⚠️ Please select a valid delivery date. Past dates are not allowed.").show();
            $(ev.currentTarget).val('');

            // Send False to backend
            rpc('/shop/set_delivery_date', {
                delivery_date: false
            }).then(function (result) {
                console.log("❌ Invalid date, cleared on sale order:", result);
            }).catch(function (err) {
                console.error("❌ Error resetting delivery date:", err);
            });

            return;
        }


        rpc('/shop/set_delivery_date', {
            delivery_date: deliveryDate
        }).then(function (result) {
            console.log("✅ Delivery date saved to order:", result);
        }).catch(function (err) {
            console.error("❌ Error saving delivery date:", err);
        });
    },
    _onClickDeliveryDate: function (ev) {
        const input = ev.currentTarget;
        if (input.showPicker) {
            input.showPicker(); // Modern browsers
        } else {
            input.focus(); // Fallback
        }
    },
});

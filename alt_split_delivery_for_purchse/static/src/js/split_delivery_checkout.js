/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { _t } from '@web/core/l10n/translation';
import { rpc } from '@web/core/network/rpc';

publicWidget.registry.WebsiteSaleCheckout.include({

    events: {
        ...publicWidget.registry.WebsiteSaleCheckout.prototype.events,
        'click .o_alt_split_delivery_plus': '_onPlus',
        'click .o_alt_split_delivery_minus': '_onMinus',
        'change .o_alt_split_delivery_qty': '_onInputChange',

        'change #split_greeting_card_checkbox': '_SplitonToggleGreetingCard',
        'change #split_delivery_note_checkbox': '_SplitonToggleDeliveryNote',

        'focusout #split_greeting_card_input': '_OnGreetingInput',
        'focusout #split_delivery_note_input': '_OnDeliveryInput',
    },
    init: function () {
        const res = this._super(...arguments);
        const order_summary = $('#order_delivery');
        const delivery_value_span = order_summary.find('.oe_currency_value');
        this.count = 1; // Default count
        this.label_name = '';
        this.label_td = '';
        this.delivery_address_row = $('#delivery_address_row')
        this.billing_address_row = $('#billing_address_row')
        if (delivery_value_span.length > 0) {
            this.label_td = order_summary.find('td').first(); // The "Delivery" td
            this.label_name = this.label_td.text().trim()
        };
        return res;
    },

    async start() {
        console.log('WebsiteSaleCheckout start extended!');
        // const superM = await this._super(...arguments);

        // Step 1: Backup `_super` before any `await`
        const _super = this._super.bind(this);

        const splitQty = await this._getSplitDeliveryQtyFromOrder();
        const ScheduleDate = await this._getScheduleDateFromOrder();
        const Notes = await this._getNotesFromSaleOrder();


        // Step 3: Now call _super safely
        const superM = await _super(...arguments);

        console.log(ScheduleDate)
        this.count = splitQty;
        this.$('.o_alt_split_delivery_qty').val(splitQty);
        if (this.label_name && this.label_td) {
            this.label_td.text(`${this.label_name} (${splitQty})`);
        }

        if (ScheduleDate?.status && ScheduleDate?.schedule_date) {
            const _date = ScheduleDate.schedule_date
            $('#toggle_delivery_date').prop('checked', true).trigger('change')
            console.log($('#toggle_delivery_date'))
            $('#delivery_date').val(_date)
        }
        await this._HideDeliveryAddress(this.count)

        return superM
    },

    _SplitonToggleGreetingCard: function (ev) {
        const checked = $(ev.currentTarget).is(':checked');
        const $input = $('#split_greeting_card_input');

        if (checked) {
            $input.show()
        } else {
            $input.hide().val('')
        }
    },

    _SplitonToggleDeliveryNote: function (ev) {
        const checked = $(ev.currentTarget).is(':checked');
        const $input = $('#split_delivery_note_input');
        if (checked) {
            $input.show()
        } else {
            $input.hide().val('')
        }
    },

    _OnGreetingInput: function (ev) {
        const values = $('#split_greeting_card_input').val()
        console.log("_OnGreetingInput is called ", values)
        if (values) {
           

            rpc('/shop/set_gretting_note', {
                gretting_note: values
            }).then(function (result) {
                console.log("✅ Delivery date saved to order:", result);
            }).catch(function (err) {
                console.error("❌ Error saving delivery date:", err);
            });
        }
    },

    _OnDeliveryInput: function (ev) {
        const values = $('#split_delivery_note_input').val()
        console.log("_OnDeliveryInput is called ", values)
        if (values) {
            

            rpc('/shop/set_delivery_note', {
                delivery_note: values
            }).then(function (result) {
                console.log("✅ Delivery date saved to order:", result);
            }).catch(function (err) {
                console.error("❌ Error saving delivery date:", err);
            });
        }
    },


    async _getNotesFromSaleOrder() {
        console.log("_getNotesFromSaleOrder is called ---------------- ")
        try {
            const result = await rpc('/get/notes', {});
            console.log(result)
            if (result.greeting_card) {
                console.log("✅ Greeting Card:", result.greeting_card);
                const getting_toggle = $('#split_greeting_card_checkbox').prop('checked', true)
                $('#split_greeting_card_input').show()
                $('#split_greeting_card_input').val(result.greeting_card);
            }
            if (result.delivery_note) {
                console.log("✅ Delivery Note:", result.delivery_note);
                const del_note_toggle = $('#split_delivery_note_checkbox').prop('checked', true)
                $('#split_delivery_note_input').show()
                $('#split_delivery_note_input').val(result.delivery_note);
            }
            return result;
        } catch (e) {
            console.error("❌ Could not fetch _getScheduleDateFromOrder from server", e);
            return { status: false, schedule_date: false };
        }
    },

    async _HideDeliveryAddress(count) {
        // console.log("geting count -- ",count)
        const radio = document.querySelector('input[name="o_delivery_radio"]:checked');
        const is_show = radio.dataset.isSupportsSplit === "True" ? true : false;
        if (is_show) {
            if (count >= 2) {
                this._updateDeliveryMethod(radio)
                this.delivery_address_row.hide()
                this.billing_address_row.hide()
                $('#warning_block').show()
            }
            else {
                this.delivery_address_row.show()
                this.billing_address_row.show()
                $('#warning_block').hide()
            }
        }
    },

    async _getScheduleDateFromOrder() {
        try {
            const result = await rpc('/get/schedule/date', {});
            return result
        }
        catch {
            console.error("❌ Could not fetch split quantity from server", e);
            return { status: false, schedule_date: false };

        }
    },

    async _getSplitDeliveryQtyFromOrder() {
        try {
            const result = await rpc('/get/current/split_qty', {});
            console.log("_getSplitDeliveryQtyFromOrder result ", result)
            return result?.split_qty || 1;
        } catch (e) {
            console.error("❌ Could not fetch split quantity from server", e);
            return 1;
        }
    },

    async _set_delivery_count(count) {
        // console.log("_set_delivery_count is called ------------")
        if (this.label_name && this.label_td) {
            this.label_td.text(`${this.label_name} (${count})`);
        } else {
            console.log("❌ Delivery price element not found.");
        }
    },
    async _setDeliveryMethod(dmId) {
        const radio = document.querySelector('input[name="o_delivery_radio"]:checked');
        const is_show = radio.dataset.isSupportsSplit === "True" ? true : false;

        var split_qty = 0;
        if (is_show) {
            split_qty = parseInt(this.$('.o_alt_split_delivery_qty').val()) || 1;
        }
        // console.log('Setting delivery method with dmId:', dmId, 'and split_qty:', split_qty);
        return await rpc('/shop/set_delivery_method', { 'dm_id': dmId, 'split_qty': split_qty });
    },
    async _updateDeliveryMethod(radio) {
        console.log('Updating delivery method for radio:', radio.dataset);
        const isSupportsSplit = radio.dataset.isSupportsSplit === "True" ? true : false;
        const isSupportsPickup = radio.dataset.isSupportsPickup === "True" ? true : false;
        if (!isSupportsSplit) {
            $('#alt_split_delivery_container').hide();
            if (this.label_name && this.label_td) {
                this.label_td.text(`${this.label_name}`);
            }
        } else {

            $('#alt_split_delivery_container').show();
            if (this.label_name && this.label_td) {
                this.label_td.text(`${this.label_name} (${this.count})`);
            }
        }

        if(isSupportsPickup){
            $('#warning_block').hide()
        }

        if(isSupportsSplit && this.count >= 2){
            $('#warning_block').show()
        }

        if (isSupportsPickup || (isSupportsSplit && this.count >= 2)) {
            console.log("Hiding delivery and billing address rows because of pickup or split delivery with count >= 2");
            this.delivery_address_row.hide()
            this.billing_address_row.hide()
        }
        else {
            console.log("Showing delivery and billing address rows because of single delivery or split delivery with count < 2");
            this.delivery_address_row.show()
            this.billing_address_row.show()
            // $('#warning_block').hide()
        }
        this._showLoadingBadge(radio);
        const result = await this._setDeliveryMethod(radio.dataset.dmId);
        this._updateAmountBadge(radio, result);
        this._updateCartSummary(result);
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
        let count = qty

        console.log('➕ Plus clicked → Qty:', qty);
        const radio = document.querySelector('input[name="o_delivery_radio"]:checked');
        this._updateDeliveryMethod(radio);
        this.count = count; // Update the count
        this._set_delivery_count(count)
        this._HideDeliveryAddress(count)
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
        let count = qty
        const radio = document.querySelector('input[name="o_delivery_radio"]:checked');
        this._updateDeliveryMethod(radio);
        this.count = count; // Update the count
        this._set_delivery_count(count)
        this._HideDeliveryAddress(count)

    },

    _onInputChange: function (ev) {
        const val = parseInt($(ev.currentTarget).val()) || 1;
        console.log('🔁 Qty changed manually:', val);

    }

});

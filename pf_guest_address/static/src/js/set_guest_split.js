/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.GuestSplitDelivery = publicWidget.Widget.extend({
    selector: '.oe_cart',

    events: {
        'click [name="guest_delivery_carrier_id"]': '_selectDeliveryMethodGuest',
        'click .address_page_split_delivery_minus': '_onMinus',
        'click .address_page_split_delivery_plus': '_onPlus',
        'click #want_fill_above_data': '_FillData',
        'change .address_page_split_delivery_qty': '_onInputChange',

        'change #_delivery_date': '_onToggleCheckbox',
        'change #guest_delivery_date': '_onInputChangeDate',
        'click #guest_delivery_date': '_onClickDeliveryDate',

        'change #guest_greeting_card_input': '_onToggleGreetingCard',
        'change #guest_delivery_note_input': '_onToggleDeliveryNote',

        'click #checkbox_is_enable_company_vat_visible' : '_onClickCheckBoxEnableVatCompany'

        
        // 'input #guest_greeting_card_text': '_onGreetingCardChange',
        // 'input #guest_delivery_note_text': '_onDeliveryNoteChange',

    },

    start: function () {
        console.log('GuestSplitDelivery Delivery Widget Initialized');
        const is_partner_sudo_id = $('#is_partner_sudo_id').val()
        console.log("----> is_partner_sudo_id", is_partner_sudo_id);
        const mail_class = $('#div_email_public').hasClass('guest-enabled-True')
        console.log("----> mail_class", mail_class);
        if(mail_class){
            console.log("--mail_class %",mail_class)
            const guestMail = $('#div_email_public')
            if (guestMail) {
                guestMail.hide()
            }
        }

        $('#personal_email').on('input', function () {
            $('#o_email').val($(this).val());
        });

        $('#personal_company, #personal_vat').attr('required', 'required');

        if(is_partner_sudo_id){
            $('#div_email').hide()
        }

        return this._super.apply(this, arguments);
    },

    _onClickCheckBoxEnableVatCompany(ev){
        console.log("checkbox_is_enable_company_vat_visible ---> ",ev)
        if($("#show_company_fields_checkbox").prop('checked') == true){
            console.log("------------ \n",$('#company_vat_block'))
            $('#company_vat_block').show()
            $('#personal_vat').attr('required', 'required'); 
            $('#personal_company').attr('required', 'required'); 

        }
        else{
            $('#company_vat_block').hide()
            $('#company_vat_block').find('input').each(function(){
                $(this).val('');
            })
            $('#personal_vat').removeAttr('required');
            $('#personal_company').removeAttr('required');

        }

    },

    _onToggleGreetingCard: function (ev) {
        const checked = $(ev.currentTarget).is(':checked');
        const $input = $('#guest_greeting_card_text');

        if (checked) {
            $input.show().attr('required', true);
        } else {
            $input.hide().val('').removeAttr('required');
        }
    },

    _onToggleDeliveryNote: function (ev) {
        const checked = $(ev.currentTarget).is(':checked');
        const $input = $('#guest_delivery_note_text');

        if (checked) {
            $input.show().attr('required', true);
        } else {
            $input.hide().val('').removeAttr('required');
        }
    },

    _onGreetingCardChange: function (ev) {
        const value = $(ev.currentTarget).val();
        
    },

    _onDeliveryNoteChange: function (ev) {
        const value = $(ev.currentTarget).val();
       
    },

    _onToggleCheckbox: function (ev) {
        const checked = $(ev.currentTarget).is(':checked');
        const $input = $('#guest_delivery_date');
        const $errorDiv = $('#delivery_date_error');

        if (checked) {
            $input.show().attr('required', true);
        } else {
            $input.hide().val('').removeAttr('required');
            $errorDiv.hide().text('');
        }
    },

    _getOrderDateValue() {
        return $('#guest_delivery_date').val();
    },

    _onInputChangeDate: function (ev) {
        const deliveryDate = this._getOrderDateValue();
        const $errorDiv = $('#delivery_date_error');
        const checkboxChecked = $('#_delivery_date').is(':checked');

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

    async _updateDeliveryAddressUI({ fillDummy = false, hide = false, warning = false }) {
        console.log("_updateDeliveryAddressUI is called", fillDummy, hide, warning)
        // const $fields = $('#form_title, #div_name, #div_phone, #company_name_div, #div_vat, #div_street, #div_street2, #div_city, #div_zip, #div_country, #div_state , #shipping_address_label');
        const $fields = $('#form_title, #div_name, #div_phone, #company_name_div, #div_vat, #div_street, #div_street2, #div_city, #shipping_address_label, #div_state');

        if (fillDummy) {
            const personal_name = $('#personal_name').val();
            const personal_phone = $('#personal_phone').val();
            const personal_email = $('#personal_email').val();
            const personal_company = $('#personal_company').val();
            const personal_vat = $('#personal_vat').val();

            $('#o_name').val(personal_name)
            $('#o_phone').val(personal_phone)
            $('#o_company_name').val(personal_company)
            $('#o_vat').val(personal_vat || '')
            $('#o_email').val(personal_email)
            $('#o_country_id').val(102);

            // $('#o_state_id').append('<option value="1809">ISRAEL</option>');
            // $('#o_state_id').val('1809').trigger('change');
            //$('#o_country_id').val(102)
            // $('#o_country_id').on('change', function () {
            //     setTimeout(() => {
            //         $('#o_state_id').val(1809);
            //     }, 500); // Delay long enough for Odoo to populate states
            // });
            // setTimeout(() => {
            //     $('#o_state_id').val(1809);
            // }, 300);

            // comment this code on sep 1 2025 below 4 lines
            $('#o_street').val('israel')
            $('#o_street2').val('israel')
            $('#o_city').val('israel')
            $('#o_zip').val('000')
        }
        else {
            $('#o_name, #o_phone, #o_company_name, #o_vat, #o_email', '#o_street', '#o_street2', '#o_city').val('');
        }

        if (hide) {
            $fields.hide()
            $('#fill_address_div').hide()
        }

        else {
            $fields.show();
            $('#fill_address_div').show();
        }

        if (warning) {
            $('#warning_block').show();
        }
        else {
            $('#warning_block').hide();
        }

    },


    async _FillData(ev) {
        const personal_name = $('#personal_name').val();
        const personal_phone = $('#personal_phone').val();
        const personal_email = $('#personal_email').val();
        const personal_company = $('#personal_company').val();
        const personal_vat = $('#personal_vat').val();
        const isChecked = ev.currentTarget.checked;
        if (isChecked) {
            $('#o_country_id, #o_state_id').removeAttr('required');
            $('#o_name').val(personal_name)
            $('#o_phone').val(personal_phone)
            $('#o_company_name').val(personal_company)
            $('#o_vat').val(personal_vat || '')
            $('#o_email').val(personal_email)
            
            // $('#o_street').val('israel')
            // $('#o_street2').val('israel')
            // $('#o_city').val('israel')
            // $('#o_zip').val('000')

            $('#o_country_id').val(102);
            // $('#o_state_id').append('<option value="1809">ISRAEL</option>');
            // $('#o_state_id').val('1809').trigger('change');
        }
        else {
            $('#o_name, #o_phone, #o_company_name, #o_vat, #o_email').val('');
        }
    },

    async _selectDeliveryMethodGuest(ev) {

        var requiredFields = []
        const flag_is_enable_company_vat_visible = $('#flag_is_enable_company_vat_visible').val()
        if (flag_is_enable_company_vat_visible === 'True'){
             requiredFields = ['#personal_name', '#personal_phone', '#personal_email'];
        }
        else{
             requiredFields = ['#personal_name', '#personal_phone', '#personal_email' , '#personal_company' , '#personal_vat'];
        }
        // const requiredFields = ['#personal_name', '#personal_phone', '#personal_email'];

        let missing = [];

        for (const selector of requiredFields) {
            const val = $(selector).val()?.trim();
            if (!val) {
                missing.push(selector);
            }
        }

        if (missing.length > 0) {
            ev.preventDefault();
            alert("⚠️ Please fill in your personal details before selecting a delivery method.");
            $(missing[0]).focus();  // Focus on the first missing field
            return;
        }
        const checkedRadio = ev.currentTarget;
        await this._updateDeliveryMethodGuest(checkedRadio);
    },

    /**
     * Set the delivery method on the order and update the price badge and cart summary.
     *
     * @private
     * @param {HTMLInputElement} radio - The radio button linked to the delivery method.
     * @return {void}
     */
    async _updateDeliveryMethodGuest(radio) {
        console.log("_updateDeliveryMethodGuest is ", radio)
        if (radio) {
            const dm_id = radio.dataset.dmId;

            const qtyInput = this.$('.address_page_split_delivery_qty');
            const is_SupportsSplit = radio.dataset.isSupportsSplit === "True" ? true : false;
            const is_SupportsSelfPickUp = radio.dataset.isSupportsPickup === "True" ? true : false;

            if (!is_SupportsSelfPickUp && !is_SupportsSplit) {
                await this._updateDeliveryAddressUI({ fillDummy: false, hide: false, warning: false });
            }

            if (is_SupportsSelfPickUp) {
                await this._updateDeliveryAddressUI({ fillDummy: true, hide: true, warning: false });
            }

            if (is_SupportsSplit && qtyInput.val() < 2) {
                await this._updateDeliveryAddressUI({ fillDummy: false, hide: false, warning: false });
                $('#o_street').val('')
                $('#o_street2').val('')
                $('#o_city').val('')
                $('#o_zip').val('')
            }
            // else {
            //  await this._updateDeliveryAddressUI({ hide: false });
            // }

            if (!is_SupportsSplit) {
                $('#pf_guest_delivery_split_show').hide();
                qtyInput.val(1)
            } else {
                $('#pf_guest_delivery_split_show').show();
            }

            const split_qty = qtyInput.val()
            if (dm_id) {
                try {
                    const result = await rpc('/shop/set_delivery_method', {
                        dm_id: parseInt(dm_id),
                        split_qty: split_qty,
                    });
                    console.log("✅ Delivery method set:", result);
                }
                catch (error) {
                    console.error("❌ Failed to set delivery method:", error);

                }
            }


            // if (qtyInput.length) {
            //     this._onInputChange({ currentTarget: qtyInput[0] });
            // }

        }

    },
    _onPlus: function (ev) {
        // const selected = this._getSelectedDeliveryMethod();
        console.log('🔼 Plus clicked for delivery method:');
        const $input = this.$('.address_page_split_delivery_qty');
        let qty = parseInt($input.val()) || 1;
        qty++;
        $input.val(qty);
        let count = qty
        // const radio = document.querySelector('input[name="o_delivery_radio"]:checked');
        // this._updateDeliveryMethod(radio);
        // this.count = count; // Update the count
        // this._set_delivery_count(count)
        $input.trigger('change');  // 👈 Trigger change event manually

        const radio = document.querySelector('input[name="guest_delivery_carrier_id"]:checked');
        if (radio) {
            this._updateDeliveryMethodGuest(radio);  // ✅ Core call
        } else {
            console.warn("⚠️ No delivery method selected!");
        }

    },

    _onMinus: function (ev) {
        // const selected = this._getSelectedDeliveryMethod();
        console.log('🔽 Minus clicked for delivery method:');
        const $input = this.$('.address_page_split_delivery_qty');
        let qty = parseInt($input.val()) || 1;
        if (qty > 1) {
            qty--;
            $input.val(qty);
        }
        $input.trigger('change');  // 👈 Trigger change event manually
        // let count = qty
        // const radio = document.querySelector('input[name="o_delivery_radio"]:checked');
        // this._updateDeliveryMethod(radio);
        // this.count = count; // Update the count
        // this._set_delivery_count(count)
        const radio = document.querySelector('input[name="guest_delivery_carrier_id"]:checked');
        if (radio) {
            this._updateDeliveryMethodGuest(radio);  // ✅ Core call
        } else {
            console.warn("⚠️ No delivery method selected!");
        }

    },

    async _onInputChange(ev) {
        const value = parseInt($(ev.currentTarget).val()) || 0;
        console.log("now input values is $", value)
        const $fields = $('#form_title, #div_name, #div_phone, #company_name_div, #div_vat, #div_street, #div_street2, #div_city, #div_zip, #div_country, #div_state');
        if (value >= 2) {
            await this._updateDeliveryAddressUI({ fillDummy: true, hide: true, warning: true });

        } else {
            await this._updateDeliveryAddressUI({ hide: false, });

        }
    }


});

/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import websiteSaleAddress from "@website_sale/js/address";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.websiteSaleAddress.include({
    events: {
        ...publicWidget.registry.websiteSaleAddress.prototype.events,
        'change #same_as_delivery': '_onToggleBillingCheckbox',
        // 'change select[name="invoice_country_id"]': '_changeCountryDelivery',
        // "change select[name='invoice_o_state_id']": "_onChangeStateDelivery",

    },    /**
     * @override
     */
    init: function () {
        const res = this._super(...arguments);
        this.is_new_customer = parseInt(this.addressForm.new_customer?.value);
        // this.ShippingFormValidation()

        return res;
    },
    start() {
        const res = this._super(...arguments);
        this._toggleBillingForm(); // handle default state
        return res;
    },  

    // ShippingFormValidation: function (validation=false) {
    //     console.log("ShippingFormValidation called");
    //     console.log("is_new_customer: ", this.is_new_customer);
    //     console.log("validation: ", validation);
    //     var addr_fields = ['invoice_name','invoice_phone','invoice_email','invoice_street','invoice_city'];

    //     if (this.is_new_customer && validation) {
    //         // add two new item to requiredFields
    //         // push only if not already present
    //         addr_fields.forEach((item) => {
    //             if (!this.requiredFields.includes(item)) {
    //                 this.requiredFields.push(item);
    //                 this._markRequired(item, true);
    //             }
    //         });
            
       
    //     }else{

    //         // remove_item from requiredFields
            
    //         addr_fields.forEach((item) => {
    //             var removeItem = this.requiredFields.indexOf(item);
    //             if (removeItem > -1) {
    //                 this.requiredFields.splice(removeItem, 1);
    //                 this._markRequired(item, false);
    //             }
    //         });
    //     }
        
    //     console.log("requiredFields: ", this.requiredFields);
    //     return true; // return true if validation passes, false otherwise
    // },  

    /**
     * @private
     * @param {Event} ev
     */
    // _onChangeStateDelivery(ev) {
    //     return Promise.resolve();
    // },

     /**
     * @private
     */
    // async _changeCountryDelivery(init=false) {
    //     init = false
    //     console.log("Changing country for Delivery: ");
        
    //     const DeliverycountryId = parseInt(this.addressForm.invoice_country_id.value);
    //     console.log("DeliverycountryId --------- : ",DeliverycountryId);

    //     if (!DeliverycountryId) {
    //         return;
    //     }

    //     const data = await rpc(
    //         `/shop/country_info/${parseInt(DeliverycountryId)}`,
    //         {address_type: this.addressType},
    //     );

    //     if (data.phone_code !== 0) {
    //         this.addressForm.phone.placeholder = '+' + data.phone_code;
    //     } else {
    //         this.addressForm.phone.placeholder = '';
    //     }

    //     // populate states and display
    //     var selectStates = this.addressForm.invoice_state_id;
    //     console.log("int: ", init);
    //     console.log("selectStates.options.length: ", selectStates.options.length);
        
    //     if (!init || selectStates.options.length === 1) {
    //         console.log("Populating states for Delivery country: ", DeliverycountryId);
    //         // dont reload state at first loading (done in qweb)
    //         if (data.states.length || data.state_required) {
    //             // empty existing options, only keep the placeholder.
    //             selectStates.options.length = 1;

    //             // create new options and append them to the select element
    //             data.states.forEach((state) => {
    //                 let option = new Option(state[1], state[0]);
    //                 // Used by localizations
    //                 option.setAttribute('data-code', state[2]);
    //                 selectStates.appendChild(option);
    //             });
    //             this._showInput('invoice_state_id');
    //             this._markRequired('invoice_state_id', true);
    //         } else {
    //             this._hideInput('invoice_state_id');
    //             this._markRequired('invoice_state_id', false);
    //         }
    //     }

    // },

    _onToggleBillingCheckbox: function () {
        console.log("1st called ------------")

        this._toggleBillingForm();
    }, _toggleBillingForm: function () {
        console.log("2nd called ------------")
        const checkbox = document.querySelector('#same_as_delivery');
        const billingForm = document.querySelector('#billing_address_form'); 
        const title = document.querySelector('#form_title');

        if (checkbox && billingForm && title) {
            if (!checkbox.checked){
                // title.textContent = 'Fill in your Billing Address';
                title.textContent = 'מלא את כתובת החיוב שלך';
                billingForm.style.display = '';
                // this.ShippingFormValidation(true);
            } else {
                // title.textContent = 'Where You Want To Deliver Your Order ?';
                title.textContent = 'לאן אתה רוצה לשלוח את ההזמנה שלך?';
                billingForm.style.display = 'none';
                // this.ShippingFormValidation(false);
            }
        }
    },
});


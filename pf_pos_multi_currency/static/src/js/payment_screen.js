/** @odoo-module **/

import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { useRef } from "@odoo/owl";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";

// patch the PaymentScreen class
patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        // console.log("---> patch(PaymentScreen.prototype is called")

        this.root = useRef('PartialPayment');
        this.button = useRef('PartialPaymentButton');              
    },                   
    //Partial Payment Button Functionality
    PartialPaymentButton() {
        if (!this.currentOrder.get_partner()) {
                this.env.services.popup.add(ErrorPopup, {
                        title: _t("No partner selected"),
                        body: _t("Please select partner."),
                });
            return false;
        };
        if (this.currentOrder.partial_payment === true) {
            this.currentOrder.partial_payment = false;
            var validate = this.root.el || this.button.el;
            validate.classList.add('disabled');
        } else if(this.currentOrder.get_partner()){
            this.currentOrder.partial_payment = true;
            this.currentOrder.is_partial_payment = true;
            this.currentOrder.custom_currency_id = this.currentOrder.pricelist.currency_id[0];
            var validate = this.root.el || this.button.el;
            validate.classList.remove('disabled');                
        }
    },
    async AddShippingButton(){        
        // console.log("pass....",this.orm);
        const shipping_methods = await this.orm.call('delivery.carrier','search_read',[[]]);
        // console.log("..............shipping_methods.........",shipping_methods);
        const { confirmed, payload: selected_method } = await this.popup.add(SelectionPopup, {
            title: 'Select Shipping Method',
            list: shipping_methods.map(method => ({
                id: method.id,
                label: method.name,
                item: method
            })),
        });
        if (confirmed) {                        
            this.currentOrder.add_shipping_line(selected_method.product_id[0],selected_method.fixed_price);
            this.currentOrder.addshipping=true;
        }    
    },
    //Validate Payment Button Functionality
    async validateOrder(isForceValidate) {
        // console.log("...........this.currentOrder.partial_payment.........",this.currentOrder.partial_payment);
        if (!this.currentOrder.partial_payment){
            if(this.currentOrder.get_partner()){
                await super.validateOrder(...arguments);
            }
            else{
                this.env.services.popup.add(ErrorPopup, {
                    title: _t("No partner selected"),
                    body: _t("Please select partner."),
            });
            return false;
            }        
        }
        else {
            if(this.currentOrder.get_partner()){
                if(!this.currentOrder.to_invoice){
                    this.env.services.popup.add(ErrorPopup, {
                        title: _t("Cannot Validate This Order"),
                        body: _t("You need to Set Invoice for Validating Partial Payments."),
                    });
                    return false;
                }
                else if(!this.currentOrder.get_due()){
                    this.env.services.popup.add(ErrorPopup, {
                        title: _t("Cannot Validate This Order"),
                        body: _t("The Amount is Fully Paid Disable Partial Payment to Validate this Order."),
                    });
                    return false;
                }
                else{
                    await super.validateOrder(...arguments);
                }                
            }
            else{
                this.env.services.popup.add(ErrorPopup, {
                    title: _t("No partner selected"),
                    body: _t("Please select partner.")});
                return false;
            }                                  
            this.currentOrder.is_partial_payment = true;
            // console.log("..........................this.currentrder.is_partial_payment",this.currentOrder.is_partial_payment);
            // console.log("..........................this.currentOrder.server_id",this.currentOrder.server_id);           
            await this._isOrderValid(isForceValidate);
            if (this.currentOrder.server_id){            
                const url = `/web#id=${this.currentOrder.server_id}&cids=1&menu_id=367&action=589&model=pos.order&view_type=form`;
                await window.open(url, '_blank');
            }     
            await this._finalizeValidation();
        }      
        }                        
    
});

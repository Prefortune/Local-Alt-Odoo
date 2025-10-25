/** @odoo-module **/

import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { PaymentScreenStatus } from "@point_of_sale/app/screens/payment_screen/payment_status/payment_status";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";

patch(PaymentScreenStatus.prototype, {

    get remainingText() {
        console.log("remainingText is called from custom addons \n")

        if (this.props.order.get_is_pricelist_currency()) {
            var currency_id = this.props.order.pricelist.currency_id[0];
            var currency = this.props.order.pos.db.currency_by_id[currency_id];
            var from_currency_id = this.props.order.pos.config.currency_id[0];
            var from_currency = this.props.order.pos.db.currency_by_id[from_currency_id];
            var total_with_tax_converted = this.props.order.pos.convert_currency(from_currency, currency, this.props.order.get_total_with_tax());
            var total_paid_converted = this.props.order.get_total_paid();
            // var total_paid_converted =  this.props.order.pos.convert_currency(from_currency, currency, this.props.order.get_total_paid())          
            var due = total_with_tax_converted.toFixed(2) - total_paid_converted + this.props.order.get_rounding_applied();
            due = this.props.order.pos.convert_currency(currency, from_currency, due)
            return this.env.utils.formatCurrency(
                due > 0 ? due : 0
            );
            // return super.remainingText;
        } else {

            return super.remainingText;
        }
    },

    get changeText() {
        console.log("changeText is called from custom addons \n")
        if (this.props.order.get_is_pricelist_currency()) {
            // console.log("if is called changeText -------------------------")

            var currency_id = this.props.order.pricelist.currency_id[0];
            var currency = this.props.order.pos.db.currency_by_id[currency_id];
            var from_currency_id = this.props.order.pos.config.currency_id[0];
            var from_currency = this.props.order.pos.db.currency_by_id[from_currency_id];

            var total_with_tax_converted = this.props.order.pos.convert_currency(from_currency, currency, this.props.order.get_total_with_tax());
            // console.log("total_with_tax_converted ----------------------------------- ", total_with_tax_converted);

            var total_paid_converted = this.props.order.get_total_paid();
            // console.log("total_paid_converted ------------------------- ", total_paid_converted);

            var change = total_with_tax_converted - total_paid_converted - this.props.order.get_rounding_applied();
            // console.log("raw change (target currency): ", change);

            // Convert the raw change (even if negative) back to base currency
            var converted_change = this.props.order.pos.convert_currency(currency, from_currency, change);
            // console.log("converted change (base currency): ", converted_change);

            // Only display POSITIVE change (i.e., what we return to the customer)
            const final_change = Math.max(0, converted_change);
            // console.log("final change shown to user: ", final_change);

            return this.env.utils.formatCurrency(final_change);
        } else {
            // console.log("else is called changeText -------------------------", super.changeText)
            return super.changeText
        }
    }
});

patch(PaymentScreen.prototype, {
    confirmPayment() {
        const customTotal = this.props.order.get_total_amount();
        const currencyName = this.state.currency.name;
        if (this.state.paymentMethod) {
            this.state.paymentMethod.processPayment(customTotal, this.state.order, currencyName);
        } else {
            super.confirmPayment();
        }
    },
    setup() {
        super.setup();
        // console.log(" -------- > patch(PaymentScreen.prototype)  is called");

    },
    
    updateSelectedPaymentline(amount = false) {
        var res = super.updateSelectedPaymentline(amount);
        console.log("updateSelectedPaymentline is called From Custom Addons \n",amount);
        // console.log(".....................res....",res,amount,this.numberBuffer.get(),this.selectedPaymentLine);
        // if (this.selectedPaymentLine) {
        //     if (this.numberBuffer.get() != null) {
        //         this.selectedPaymentLine.is_payment_manually = true;
        //     }
        // }
        // if (this.selectedPaymentLine) {
        //     if (this.numberBuffer.get() != null) {
        //         // console.log(".............this.numberBuffer.get().........",this.numberBuffer.getFloat());
        //         // if(this.currentOrder.get_is_pricelist_currency()){                    
        //         //     var currency_id = this.currentOrder.pricelist.currency_id[0];
        //         //     var currency = this.pos.db.currency_by_id[currency_id];
        //         //     var from_currency_id = this.pos.config.currency_id[0];
        //         //     var from_currency = this.pos.db.currency_by_id[from_currency_id];                    
        //         //     var amount = this.pos.convert_currency(currency, from_currency, this.numberBuffer.getFloat()); 
        //         //     console.log(".................amount...........",amount);                   
        //         this.selectedPaymentLine.set_amount(this.numberBuffer.get());
        //         // }               
        //     }
        // }
        // console.log("...........................after...........................",this.selectedPaymentLine);
        return res
    },
    deletePaymentLine(cid) {
        super.deletePaymentLine(cid);
        if (this.paymentLines.length == 0) {
            this.currentOrder.set_is_pricelist_currency(true);
        }
    },
    async _finalizeValidation() {
        console.log("_finalizeValidation called from custom addons")
        var currency_id = this.currentOrder.pricelist.currency_id[0];
        var currency = this.pos.db.currency_by_id[currency_id];
        var from_currency_id = this.pos.default_pricelist.currency_id[0];
        var from_currency = this.pos.db.currency_by_id[from_currency_id];
        if (this.pos.currentOrder) {
            if (this.currentOrder.get_is_pricelist_currency()) {
                var total = this.currentOrder.get_total_with_tax();
                // console.log("..............before...........total..........",total);
                total = this.pos.convert_currency(from_currency, currency, total);
                // console.log("........................total.................",total);
                if (this.currentOrder.pricelist && this.currentOrder.pricelist.currency_id) {
                    if (this.pos.pay_currency_amount && this.pos.pay_currency_amount[this.currentOrder.pricelist.currency_id[0]]) {
                        this.pos.pay_currency_amount[this.currentOrder.pricelist.currency_id[0]] = this.pos.pay_currency_amount[this.currentOrder.pricelist.currency_id[0]] + parseFloat(total.toFixed(2))
                    } else {
                        this.pos.pay_currency_amount[this.currentOrder.pricelist.currency_id[0]] = parseFloat(total.toFixed(2))
                    }
                }
            } else {
                if (this.pos.config.currency_id) {
                    if (this.pos.pay_currency_amount && this.pos.pay_currency_amount[this.pos.config.currency_id[0]]) {
                        this.pos.pay_currency_amount[this.pos.config.currency_id[0]] = this.pos.pay_currency_amount[this.pos.config.currency_id[0]] + parseFloat(this.currentOrder.get_total_with_tax().toFixed(2))
                    } else {
                        this.pos.pay_currency_amount[this.pos.config.currency_id[0]] = parseFloat(this.currentOrder.get_total_with_tax().toFixed(2))
                    }
                }
            }
        }
        await super._finalizeValidation();
    }
});

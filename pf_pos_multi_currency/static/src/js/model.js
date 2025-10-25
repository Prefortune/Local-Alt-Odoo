/** @odoo-module */

import { PosDB } from "@point_of_sale/app/store/db";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order, Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { formatMonetary } from "@web/views/fields/formatters";
import {
    roundPrecision as round_pr,
    floatIsZero,
} from "@web/core/utils/numbers";
import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { contextualUtilsService } from "@point_of_sale/app/utils/contextual_utils_service";


patch(contextualUtilsService, {
    async start(env, { pos, localization }) {
        // console.log("---------> patch(contextualUtilsService) is called")
        const supercontextualUtilsService = await super.start(...arguments);
        const convert_currency = (from_currency, currency, amount) => {
            var screenlist = [];
            if (!pos.get_order().get_is_pricelist_currency()) {
                screenlist.push("PaymentScreen");
                screenlist.push("ReceiptScreen");
            }
            if ((currency.rate) && (from_currency.rate) && pos.get_order().get_screen_data() && !screenlist.includes(pos.get_order().get_screen_data().name)) {
                console.log("amount before \n", amount);  
                amount = (amount) * (currency.rate / (1));
                console.log("amount after\n", amount, currency, from_currency);
                console.log("currency \n", currency.rate);
                console.log("from_currency \n", from_currency.rate);
                return amount;
            } else {
                return amount;
            }
        }
        const cusformatCurrency = (value, hasSymbol = true) => {
            console.log("cusformatCurrency called from custom addons \n")
            // console.log("---------> cusformatCurrency is called")

            if (!hasSymbol) {
                var currency_id = pos.get_order().pricelist.currency_id[0];
                var currency = pos.db.currency_by_id[currency_id];
                return formatMonetary(value, {
                    currencyId: currency.id,
                    noSymbol: !hasSymbol,
                });
            }
            else {
                if (pos.default_pricelist) {
                    if (pos.get_order().pricelist.currency_id) {
                        var currency_id = pos.get_order().pricelist.currency_id[0];
                        var currency = pos.db.currency_by_id[currency_id];
                        var from_currency_id = pos.default_pricelist.currency_id[0];
                        var from_currency = pos.db.currency_by_id[from_currency_id];
                        const amount = convert_currency(from_currency, currency, value);
                        // console.log(".......................amount...",amount,hasSymbol);
                        value = amount;
                        return formatMonetary(value, {
                            currencyId: currency.id,
                            noSymbol: !hasSymbol,
                        });
                    }
                    else {
                        return formatMonetary(value, {
                            currencyId: currency.id,
                            noSymbol: !hasSymbol,
                        });
                    }
                }
                else {
                    return formatMonetary(value, {
                        currencyId: currency.id,
                        noSymbol: !hasSymbol,
                    });
                }
            }
        }
        env.utils.formatCurrency = cusformatCurrency;
    }


});


patch(PosDB.prototype, {
    add_currencies(currencies) {
        // console.log("---------> add_currencies")
        if (!this.currencies) {
            this.currencies = [];
            this.currency_by_id = {};
        }
        if (!currencies instanceof Array) {
            currencies = [currencies];
        }
        for (var i = 0, len = currencies.length; i < len; i++) {
            var currency = currencies[i];
            this.currencies.push(currency);
            this.currency_by_id[currency.id] = currency;
        }
    }
});

patch(PosStore.prototype, {
    /**
     * @override
     */
    async setup() {
        await super.setup(...arguments);
        this.pay_currency_amount = {}
        // console.log("---------> patch(PosStore.prototype) is called")
    },
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.currencies = loadedData['res.currency'] || [];

        this.db.add_currencies(this.currencies);
        if (loadedData['amount_by_currency']) {
            self.pay_currency_amount = loadedData['amount_by_currency']
        }
        this.limit = 100000;
    },
    convert_currency(from_currency, currency, amount) {

        var screenlist = []
        if (!this.get_order().get_is_pricelist_currency()) {
            screenlist.push("PaymentScreen")
            screenlist.push("ReceiptScreen")
        }
        if (parseFloat(currency.rate) > 0.0 && parseFloat(from_currency.rate) > 0.0 && this.get_order().get_screen_data() && !screenlist.includes(this.get_order().get_screen_data().name)) {
            amount = parseFloat(amount) * (parseFloat(currency.rate) / parseFloat(from_currency.rate));
            console.log("convert_currency is called from custom addons \n", amount, currency.rate, from_currency.rate)
            return amount;
        } else {
            return amount;
        }
    },

    async _save_to_server(orders, options) {
        if (orders.length > 0) {
            for (let i = 0, len = orders[0].data.statement_ids.length; i < len; i++) {
                // console.log(".............this.orders[0].paymentlines[i]............",this.orders[0].paymentlines[i].amount,this.orders[0].paymentlines[i].order.pricelist.currency_id[1]);
                if (this.orders[0].paymentlines[i].amount) {
                    var currency_id = this.get_order().pricelist.currency_id[0];
                    var currency = this.db.currency_by_id[currency_id];
                    // console.log("........................currency...",currency); 
                    var from_currency_id = this.default_pricelist.currency_id[0];
                    var from_currency = this.db.currency_by_id[from_currency_id];
                    // var amount=this.convert_currency(from_currency,currency,this.orders[0].paymentlines[i].amount);
                    orders[0].data.statement_ids[i][2].currency_amount = this.orders[0].paymentlines[i].amount;
                    orders[0].data.statement_ids[i][2].payment_currency = currency.name;
                } else {
                    orders[0].data.statement_ids[i][2].currency_amount = ""
                    orders[0].data.statement_ids[i][2].payment_currency = ""
                }
            }
        }
        if (!orders || !orders.length) {
            return Promise.resolve([]);
        }
        this.set_synch("connecting", orders.length);
        options = options || {};
        var order_ids_to_sync = orders.map((o) => o.id);
        for (const order of orders) {
            order.to_invoice = options.to_invoice || false;
        }
        const orm = options.to_invoice ? this.orm : this.orm.silent;
        try {
            const serverIds = await orm.call(
                "pos.order",
                "create_from_ui",
                [orders, options.draft || false],
                {
                    context: this._getCreateOrderContext(orders, options),
                }
            );
            for (const serverId of serverIds) {
                const order = this.env.services.pos.orders.find(
                    (order) => order.name === serverId.pos_reference
                );

                if (order) {
                    order.server_id = serverId.id;
                }
            }
            for (const order_id of order_ids_to_sync) {
                this.db.remove_order(order_id);
            }
            this.failed = false;
            this.set_synch("connected");
            return serverIds;
        } catch (error) {
            if (error.code === 200) {
                if ((!this.failed || options.show_error) && !options.to_invoice) {
                    this.failed = error;
                    this.set_synch("error");
                    throw error;
                }
            }
            this.set_synch("disconnected");
            throw error;
        }
    }
});

patch(Order.prototype, {



    setup() {
        super.setup(...arguments);
        // console.log("---> patch(Order.prototype) is called")
        this.partial_payment = false;
        // console.log("....................this.is_partial_payment",this.is_partial_payment);
        this.is_partial_payment = this.is_partial_payment || false;
        this.is_pricelist_currency_payment = this && this.pos && this.pos.config ? true : false;
        this.shipping_amount = 0;
        this.shipping_method = null;
        this.addshipping = false;
    },

    _convert_currency_amount(amount) {
        // try {
        //     const from_currency = this.pos.currency[0];
        //     console.log("from_currency $$$ ", from_currency);
        //     const to_currency = this.pricelist && this.pricelist.currency_id
        //         ? this.pos.db.currency_by_id[this.pricelist.currency_id[0]]
        //         : from_currency;

        //     console.log("to_currency $$$ ", to_currency);
            
        //     if (
        //         from_currency &&
        //         to_currency &&
        //         from_currency.id !== to_currency.id &&
        //         from_currency.rate &&
        //         to_currency.rate
        //     ) {
        //         return round_pr(
        //             amount * (to_currency.rate / from_currency.rate),
        //             to_currency.rounding || 0.01
        //         );
        //     }
        // } catch (err) {
        //     console.warn("Currency conversion failed", err);
        // }
        return amount; // fallback
    },

    get_due(paymentline) {
        const from_currency_id = this.pos.default_pricelist.currency_id[0];
        const to_currency_id = this.pricelist.currency_id[0];
        const from_currency = this.pos.db.currency_by_id[from_currency_id];
        const to_currency = this.pos.db.currency_by_id[to_currency_id];

        let due = 0;

        if (!paymentline) {
            due = this.get_total_with_tax() - this.get_total_paid() + this.get_rounding_applied();
            due = (due) * (40.20 / (1));

            console.log("IF get_due BEFORE currency convert =>", due);
        } else {
            due = this.get_total_with_tax();
            const lines = this.paymentlines;
            for (let i = 0; i < lines.length; i++) {
                if (lines[i] === paymentline) break;
                due -= lines[i].get_amount();
            }
            console.log("ELSE get_due BEFORE currency convert =>", due);
        }

        // const due_final = (1 !== 40)
        //     ? due * (40.201005025126 / 1)
        //     : due;



        console.log("Converted Due =>", due);
        return round_pr(due, this.pos.currency.rounding);
    },
    set_partner(partner) {
        this.assert_editable();
        this.partner = partner;
        // this.updatePricelistAndFiscalPosition(partner);
    },
    set_shipping_method: function (shipping_method) {
        this.shipping_method = shipping_method;
        this.trigger('change', this);
    },
    set_shipping_amount: function (amount) {
        this.shipping_amount = amount;
        this.trigger('change', this);
    },
    add_shipping_line: function (shipping_product_id, shipping_amount) {
        var shipping_product = this.pos.db.get_product_by_id(shipping_product_id);
        // console.log("..................shipping_product....",shipping_product);
        if (shipping_product) {
            this.add_product(shipping_product, {
                price: shipping_amount,
            });
        }
        this.get_total_with_tax();
    },
    get_shipping_method: function () {
        return this.shipping_method;
    },
    get_shipping_amount: function () {
        return this.shipping_amount;
    },
    set_order_suggestion(suggestion) {
        this.is_partial_payment = is_partial_payment;
    },
    set_is_pricelist_currency(is_pricelist_currency_payment) {
        this.is_pricelist_currency_payment = is_pricelist_currency_payment;
    },
    get_is_pricelist_currency() {
        return this.is_pricelist_currency_payment;
    },
    // --------------------------------------------------------------
    get_total_paid() {
        // console.log("****** main method called get_total_paid")

        const total = this.paymentlines.reduce((sum, paymentLine) => {
            if (paymentLine.is_done()) {
                sum += paymentLine.get_amount();
            }
            return sum;
        }, 0);
        const rounded = round_pr(total, this.pos.currency.rounding);
        return this._convert_currency_amount(rounded);
        // return round_pr(
        //     this.paymentlines.reduce(function (sum, paymentLine) {
        //         if (paymentLine.is_done()) {
        //             sum += paymentLine.get_amount();
        //         }
        //         // console.log("----- sum of get_total_paid : ", sum)
        //         return sum;
        //     }, 0),
        //     // console.log("-------- this.pos.currency.rounding : ",this.pos.currency.rounding),
        //     this.pos.currency.rounding
        // );
    },
    get_total_with_tax() {
        const total = this.get_total_without_tax() + this.get_total_tax();
        return this._convert_currency_amount(total);

        // return this.get_total_without_tax() + this.get_total_tax();
    },
    get_total_without_tax() {
        return round_pr(
            this.orderlines.reduce(function (sum, orderLine) {
                return sum + orderLine.get_price_without_tax();
            }, 0),
            this.pos.currency.rounding
        );
    },
    get_tax_details() {
        var details = {};
        var fulldetails = [];

        this.orderlines.forEach(function (line) {
            var ldetails = line.get_tax_details();
            for (var id in ldetails) {
                if (Object.hasOwnProperty.call(ldetails, id)) {
                    details[id] = {
                        amount: (details[id]?.amount || 0) + ldetails[id].amount,
                        base: (details[id]?.base || 0) + ldetails[id].base,
                    };
                }
            }
        });

        for (var id in details) {
            if (Object.hasOwnProperty.call(details, id)) {
                fulldetails.push({
                    amount: details[id].amount,
                    base: details[id].base,
                    tax: this.pos.taxes_by_id[id],
                    name: this.pos.taxes_by_id[id].name,
                });
            }
        }

        return fulldetails;
    },
    get_total_tax() {

        let tax_total = 0;
        if (this.pos.company.tax_calculation_rounding_method === "round_globally") {
            const groupTaxes = {};
            this.orderlines.forEach(line => {
                const taxDetails = line.get_tax_details();
                for (const taxId in taxDetails) {
                    groupTaxes[taxId] = (groupTaxes[taxId] || 0) + taxDetails[taxId].amount;
                }
            });

            for (const taxId in groupTaxes) {
                tax_total += round_pr(groupTaxes[taxId], this.pos.currency.rounding);
            }
        } else {
            tax_total = this.orderlines.reduce((sum, orderLine) => {
                return sum + orderLine.get_tax();
            }, 0);
            tax_total = round_pr(tax_total, this.pos.currency.rounding);
        }

        return this._convert_currency_amount(tax_total);

        // if (this.pos.company.tax_calculation_rounding_method === "round_globally") {
        //     // As always, we need:
        //     // 1. For each tax, sum their amount across all order lines
        //     // 2. Round that result
        //     // 3. Sum all those rounded amounts
        //     var groupTaxes = {};
        //     this.orderlines.forEach(function (line) {
        //         var taxDetails = line.get_tax_details();
        //         var taxIds = Object.keys(taxDetails);
        //         for (var t = 0; t < taxIds.length; t++) {
        //             var taxId = taxIds[t];
        //             if (!(taxId in groupTaxes)) {
        //                 groupTaxes[taxId] = 0;
        //             }
        //             groupTaxes[taxId] += taxDetails[taxId].amount;
        //         }
        //     });

        //     var sum = 0;
        //     var taxIds = Object.keys(groupTaxes);
        //     for (var j = 0; j < taxIds.length; j++) {
        //         var taxAmount = groupTaxes[taxIds[j]];
        //         sum += round_pr(taxAmount, this.pos.currency.rounding);
        //     }
        //     return sum;
        // } else {
        //     return round_pr(
        //         this.orderlines.reduce(function (sum, orderLine) {
        //             return sum + orderLine.get_tax();
        //         }, 0),
        //         this.pos.currency.rounding
        //     );
        // }
    },
    get_change(paymentline) {
        let change;
        if (!paymentline) {
            change = this.get_total_paid() - this.get_total_with_tax() - this.get_rounding_applied();
        } else {
            change = -this.get_total_with_tax();
            const lines = this.paymentlines;
            for (let i = 0; i < lines.length; i++) {
                change += lines[i].get_amount();
                if (lines[i] === paymentline) break;
            }
        }
        const rounded = round_pr(Math.max(0, change), this.pos.currency.rounding);
        return this._convert_currency_amount(rounded);

        // if (!paymentline) {
        //     var change =
        //         this.get_total_paid() - this.get_total_with_tax() - this.get_rounding_applied();
        // } else {
        //     change = -this.get_total_with_tax();
        //     var lines = this.paymentlines;
        //     for (var i = 0; i < lines.length; i++) {
        //         change += lines[i].get_amount();
        //         if (lines[i] === paymentline) {
        //             break;
        //         }
        //     }
        // }
        // return round_pr(Math.max(0, change), this.pos.currency.rounding);
    },
    // export_as_JSON() {
    //     var json = super.export_as_JSON();
    //     console.log("BEFORE export_as_JSON called from custom module ---- \n",json)

    //     json.is_partial_payment = this.is_partial_payment;
    //     json.custom_currency_id = this.pricelist.currency_id[0];
    //     json.custom_currency_id_rate = this.pricelist.currency_id[0].rate;
    //     json.amount_paid = 1000
    //     json.amount_return = 2000
    //     json.amount_total = 1500
    //     // console.log(".........amount_total.....amount_tax............amount_return...",json.amount_total,json.amount_tax,json.amount_return) ;
    //     // console.log(".........this.get_total_paid()....",this.get_total_paid());
    //     // console.log('.........get_change........',this.pf_get_change());

    //     console.log("AFTER export_as_JSON called from custom module ---- \n",json)

    //     return json;
    // },
    // pf_get_total_paid() {
    //     var val = round_pr(
    //         this.paymentlines.reduce(function (sum, paymentLine) {
    //             if (paymentLine.is_done()) {
    //                 // console.log(".....................paymentLine.get_amount()..............",paymentLine,paymentLine.get_amount());
    //                 var currency_id = paymentLine.order.pricelist.currency_id[0];
    //                 var currency = paymentLine.pos.db.currency_by_id[currency_id];
    //                 var from_currency_id = paymentLine.pos.default_pricelist.currency_id[0];
    //                 var from_currency = paymentLine.pos.db.currency_by_id[from_currency_id];
    //                 var amount = paymentLine.pos.convert_currency(currency, from_currency, paymentLine.get_amount());
    //                 // console.log("................amount...",amount);                   
    //                 sum += amount;
    //             }
    //             return sum;
    //         }, 0),
    //         this.pos.currency.rounding
    //     );
    //     return val;

    // },
    // pf_get_change(paymentline) {
    //     console.log("pf_get_change is called from custom addons \n")

    //     if (!paymentline) {
    //         var change =
    //             this.pf_get_total_paid() - this.get_total_with_tax() - this.get_rounding_applied();
    //     } else {
    //         change = -this.get_total_with_tax();
    //         var lines = this.paymentlines;
    //         for (var i = 0; i < lines.length; i++) {
    //             var paymentLine = lines[i];
    //             change += lines[i].get_amount();
    //             var currency_id = paymentLine.order.pricelist.currency_id[0];
    //             var currency = paymentLine.pos.db.currency_by_id[currency_id];
    //             var from_currency_id = paymentLine.pos.default_pricelist.currency_id[0];
    //             var from_currency = paymentLine.pos.db.currency_by_id[from_currency_id];
    //             var amount = paymentLine.pos.convert_currency(currency, from_currency, paymentLine.get_amount());
    //             sum += amount;
    //             // console.log("................sum...",sum);   
    //             if (lines[i] === paymentline) {
    //                 break;
    //             }
    //         }
    //     }
    //     return round_pr(Math.max(0, change), this.pos.currency.rounding);
    // },
    // export_for_printing() {
    //     const receipt = super.export_for_printing(...arguments);
    //     var currency_id = this.pos.get_order().pricelist.currency_id[0];
    //     var currency = this.pos.db.currency_by_id[currency_id];
    //     var from_currency_id = this.pos.default_pricelist.currency_id[0];
    //     var from_currency = this.pos.db.currency_by_id[from_currency_id];
    //     if (currency_id != from_currency_id && receipt.tax_details && receipt.tax_details.length > 0) {
    //         receipt.tax_details.forEach((each_tax) => {
    //             each_tax['amount'] = (this.pos.convert_currency(from_currency, currency, each_tax['amount']));
    //         });
    //     }
    //     return receipt;


    // },
    // is_paid() {

    //     if (this.pos.get_order().get_is_pricelist_currency()) {
    //         var currency_id = this.pos.get_order().pricelist.currency_id[0];
    //         this.pos.get_order().custom_currency_id = this.pos.get_order().pricelist.currency_id[0];
    //         var currency = this.pos.db.currency_by_id[currency_id];
    //         var from_currency_id = this.pos.default_pricelist.currency_id[0];
    //         var from_currency = this.pos.db.currency_by_id[from_currency_id];
    //         var total_with_tax_converted = this.pos.convert_currency(from_currency, currency, this.pos.get_order().get_total_with_tax());
    //         var total_paid_converted = this.pos.get_order().get_total_paid();
    //         var due = total_with_tax_converted.toFixed(2) - total_paid_converted + this.pos.get_order().get_rounding_applied();
    //         due = this.pos.convert_currency(currency, from_currency, due);
    //         // due = this.pos.convert_currency(from_currency, currency, due);
    //         // console.log("...............................due.....",due,this);
    //         var check_paid = due.toFixed(2) <= 0 && this.check_paymentlines_rounding();
    //         console.log("is_paid is called from custom addons \n", check_paid)
    //         // console.log("..................check_paid....",check_paid);
    //         if (check_paid) {
    //             return check_paid;
    //         }
    //         else {
    //             if (this.partial_payment) {
    //                 // console.log(".................................partial");
    //                 return true;
    //             }
    //             else {
    //                 return check_paid;
    //             }
    //         }
    //     } else {
    //         var test = super.is_paid();
    //         // console.log(".........................test............",test);           
    //         return test;
    //     }
    // },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.is_partial_payment = json.is_partial_payment;
    },
});

patch(Orderline.prototype, {

    init_from_JSON(json) {
        // console.log("---> patch(Orderline.prototype is called")
        super.init_from_JSON(...arguments);
    },
    // export_as_JSON() {

    //     // const json = super.export_as_JSON(...arguments);
    //     const json = super.export_as_JSON(...arguments);
    //     // if (this.pos.get_order().pricelist) {
    //     //     var currency_id = this.pos.get_order().pricelist.currency_id[0];
    //     //     var currency = this.pos.db.currency_by_id[currency_id];
    //     //     var from_currency_id = this.pos.default_pricelist.currency_id[0];
    //     //     var from_currency = this.pos.db.currency_by_id[from_currency_id];
    //     //     var amount = this.pos.convert_currency(from_currency, currency, this.get_unit_price());
    //     //     json['price_display_one'] = amount;
    //     //     json['price_display'] = this.get_quantity() * amount;
    //     // }
    //     console.log("export_as_JSON is called from custom addons \n", json)
    //     return json;
    // },
})
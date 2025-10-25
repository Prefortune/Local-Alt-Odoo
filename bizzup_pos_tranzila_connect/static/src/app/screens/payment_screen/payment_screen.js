/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { CreatePaymentPopupWidget } from "@bizzup_pos_tranzila_connect/app/screens/create_payment/create_payment";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ask,makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ManagerPINPopup } from "@bizzup_margin_limit/app/screens/pin_popup/pin_popup"; // Import the custom popup


patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.state = useState({ inputValue: this.props.startingValue });
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
    },

    async validateOrder(isForceValidate) {
    for (const line of this.paymentLines) {
        const order_name = this.pos.get_order().name;
        const selectedCustomer = this.currentOrder.get_partner();
        if (!selectedCustomer) {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Customer Required"),
                body: _t("Please select a customer before proceeding."),
            });
            return;
        }

        const selectedCustomerID = selectedCustomer.id;
        const order_amount = line.get_amount();
        const datas = await this.orm.call('res.partner', 'get_partner_vat', [order_name], {
            amount: order_amount,
            customer: selectedCustomerID,
        });

        if (datas === false || datas === 'false') {
            this.dialog.add(ConfirmationDialog, {
                title: _t('Missing VAT'),
                body: _t('בבקשה הכנס ת.ז. עבור הלקוח לפני שתמשיך בתהליך.'),
            });
            return;
        }

        if (line.payment_method_id?.is_pos_physical_terminal) {
            const data = line.payment_method_id.tranzila_terminal_ids;
            const payment_limit = line.payment_method_id.payment_limit === false ? 0 : line.payment_method_id.payment_limit;
            const amount = line.get_amount();
            const currentPartner = this.currentOrder.get_partner();

            if (!currentPartner) {
                const confirmed = await ask(this.dialog, {
                    title: _t("Customer Required"),
                    body: _t("Please select a customer to proceed."),
                });
                if (confirmed) {
                    this.pos.selectPartner();
                }
                return false;
            }

            const partner = currentPartner.id;
            const terminals = await this.orm.call('tranzila.physical.terminal', 'get_terminals_by_ids', []);

            if (!terminals || terminals.length === 0) {
                this.dialog.add(ConfirmationDialog, {
                    title: _t('Machine ID Not Found'),
                    body: _t('Please add the Machine ID in the selected payment method to proceed.'),
                });
                return;
            }

            let limit = parseFloat(this.pos.company.limit_parameter);
            let error = parseFloat(this.pos.company.error_parameter);

            let total_amount = 0;

            let order = this.pos.get_order();
            let lines = order.get_orderlines();

            for (let line of this.paymentLines) {
                total_amount += line.get_amount()
            }
            const orderCost = order.get_total_cost();
            const orderMargin = (total_amount - orderCost) / total_amount;
            const marginPercent = orderMargin * 100;
            let limit_calculation = limit * 100;
            let error_calculation = error * 100;
            let price = 10;
            let margin = 10;

            if (limit > 0 || error > 0) {
                if (marginPercent < limit_calculation) {
                    const manager = await this.orm.call('res.users', 'check_manager_of_user', [price], {
                        cashier: this.pos.get_cashier().id,
                    });
                    if (manager) {
                        const confirmed = await makeAwaitable(this.dialog,ManagerPINPopup, {
                            margin: margin,
                        });
                        if (confirmed) {
                            const confirmed = await makeAwaitable(this.dialog, CreatePaymentPopupWidget, {
                                amount: amount,
                                paymentlimit: payment_limit,
                                order_ref: terminals,
                                partner: partner,
                            });
                            if (confirmed) {
                                await super.validateOrder(...arguments);
                            } else {
                                return;
                            }
                        }
                        else {
                            return;
                        }
                    } else {
                        // Block Order
                        this.dialog.add(ConfirmationDialog, {
                            title: _t("חסימת ריווחיות"),
                            body: _t("מרווח ההזמנה חורג מהפרמטרים. האם תרצה להמשיך?"),
                            cancel: () => {},
                            confirm: async () => {
                                const confirmed = await makeAwaitable(this.dialog, CreatePaymentPopupWidget, {
                                    amount: amount,
                                    paymentlimit: payment_limit,
                                    order_ref: terminals,
                                    partner: partner,
                                });

                                if (confirmed) {
                                    await super.validateOrder(...arguments);
                                } else {
                                    return;
                                }
                            },
                        });
                    }
                } else if (marginPercent < error_calculation) {
                    this.dialog.add(ConfirmationDialog, {
                        // Warning
                        title: _t("אזהרת ריווחיות"),
                        body: _t("המרווח שלך מסוכן. האם תרצה להמשיך?"),
                        cancel: () => {},
                        confirm: async () => {
                            const confirmed = await makeAwaitable(this.dialog, CreatePaymentPopupWidget, {
                                amount: amount,
                                paymentlimit: payment_limit,
                                order_ref: terminals,
                                partner: partner,
                            });
                            if (confirmed) {
                                await super.validateOrder(...arguments);
                            } else {
                                return;
                            }
                        },
                    });
                } else {
                    const confirmed = await makeAwaitable(this.dialog, CreatePaymentPopupWidget, {
                        amount: amount,
                        paymentlimit: payment_limit,
                        order_ref: terminals,
                        partner: partner,
                    });

                    if (confirmed) {
                        await super.validateOrder(...arguments);
                    } else {
                        return;
                    }
                }
            } else {
                const confirmed = await makeAwaitable(this.dialog, CreatePaymentPopupWidget, {
                    amount: amount,
                    paymentlimit: payment_limit,
                    order_ref: terminals,
                    partner: partner,
                });

                if (confirmed) {
                    await super.validateOrder(...arguments);
                } else {
                    return;
                }
            }
        } else {
            await super.validateOrder(...arguments);
        }
    }
    },

    async afterOrderValidation(suggestToSync = true) {
        for (const line of this.paymentLines) {
            if (line.payment_method_id?.is_pos_physical_terminal || line.payment_method_id?.is_online_payment) {
                const npay = this.currentOrder.server_id;
                if (line.payment_method_id?.is_pos_physical_terminal){
                    // call pos.order link_transaction_to_pos_order to link transaction to pos order and invoice
                    await this.orm.call('pos.order','link_transaction_to_pos_order',[npay],
                    {
                        order : this.currentOrder.id,
                        session_id : this.currentOrder.session_id.id,
                    });
                }
                const newnpay = await this.orm.call('payment.transaction', 'get_number_of_installment', [npay]);
                this.pos.get_order().selected_npay = newnpay;
           }
        }
        return await super.afterOrderValidation(...arguments);
    },
});

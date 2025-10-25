import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { ManagerPINPopup } from "@bizzup_margin_limit/app/screens/pin_popup/pin_popup"; // Import the custom popup
import { ask,makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";


patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.dialog = useService("dialog");
    },

    async validateOrder(isForceValidate) {
        for (let line of this.paymentLines) {
            let payment_method = line.payment_method_id.is_pos_physical_terminal
            if (payment_method == false) {
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
                        let manager = await this.orm.call('res.users', 'check_manager_of_user', [price], {
                                cashier: this.pos.get_cashier().id,
                            });
                        if (manager) {
                            let confirmed = await makeAwaitable(this.dialog,ManagerPINPopup, {
                                margin: margin,
                            });
                            if (confirmed) {
                               await super.validateOrder(...arguments);
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
                                await super.validateOrder(...arguments);
                                },
                            });
                         }
                    } else if (marginPercent < error_calculation) {
                        // Warning
                        this.dialog.add(ConfirmationDialog, {
                            title: _t("אזהרת ריווחיות"),
                            body: _t("המרווח שלך מסוכן. האם תרצה להמשיך?"),
                            cancel: () => {},
                            confirm: async () => {
                                await super.validateOrder(...arguments);
                            },
                        });
                    } else {
                       await super.validateOrder(...arguments);
                    }
                } else {
                    await super.validateOrder(...arguments);
                }

            }else {
                await super.validateOrder(...arguments);
            }
        }
    },

});

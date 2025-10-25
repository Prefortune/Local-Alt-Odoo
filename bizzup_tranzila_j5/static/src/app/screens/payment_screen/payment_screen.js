/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { CreatePaymentPopupWidget } from "@bizzup_pos_tranzila_connect/app/screens/create_payment/create_payment";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ask,makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";


patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.state = useState({ inputValue: this.props.startingValue });
        this.pos = usePos();
        this.dialog = useService("dialog");
        this.orm = useService("orm");
    },

    async _isOrderValid(isForceValidate) {
        for (const line of this.paymentLines) {
            const transaction_mode = line.payment_method_id.transaction_mode;
            const is_j5_enabled = this.pos.config.enable_j5_tranzila;
            const transaction = 10;
            const selectedCustomer = this.currentOrder.get_partner();

            // Proceed only if payment method is Online
            if (line.payment_method_id.is_online_payment) {
                await this.orm.call('pos.order', 'set_partner_online_order', [transaction], {
                    partner_id: selectedCustomer.id,
                    order_id: this.currentOrder.id,
                });
            }

            // Proceed only if transaction_mode is "j5" and J5 is enabled in config
            if (transaction_mode === "j5" && is_j5_enabled) {
                const npay = 10;
                await this.orm.call('payment.transaction', 'transaction_payment_mode', [npay], {
                    transaction_mode: transaction_mode,
                    order_id: this.currentOrder.id,
                });
            } else {
                return await super._isOrderValid(...arguments);
            }
        }
        return await super._isOrderValid(...arguments);
    },

});

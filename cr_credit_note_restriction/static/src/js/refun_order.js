/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";

patch(TicketScreen.prototype, {
    async setup() {
        await super.setup();
        this.allowed_employee_ids = await rpc("/pos/get_advanced_employee_ids");
    },

    async onDoRefund() {
        const currentUser = this.pos.get_cashier();
        const userId = currentUser.id;
        if (this.allowed_employee_ids?.includes(userId)) {
            return super.onDoRefund();
        }

        let pin = false;

        const pinValue = await makeAwaitable(this.dialog, NumberPopup, {
            title: _t("Manager Validation"),
            formatDisplayedValue: (x) => x.replace(/./g, "•"),
        });

        if (pinValue) {
            try {
                const response = await fetch("/pos/validate_employee_pin", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({
                        pin: pinValue,
                        allowed_ids: this.allowed_employee_ids,
                    }),
                });

                const result = await response.json();

                if (result.result.success) {
                    pin = true;
                }
            } catch (error) {
                console.error("Fetch error:", error);
            }
        }

        if (pin) {
            return super.onDoRefund();
        } else {
            this.dialog.add(AlertDialog, {
                title: _t("Invalid PIN"),
                body: _t("The PIN you entered is incorrect."),
            });
            return false;
        }
    }

});
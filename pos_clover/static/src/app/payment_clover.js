/** @odoo-module */

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class PaymentClover extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.paymentNotificationResolver = null;
    }

    _show_error(msg, title = _t("Clover Error")) {
        this.env.services.dialog.add(AlertDialog, {
            title: title,
            body: msg,
        });
    }

    send_payment_request(uuid) {
        super.send_payment_request(uuid);
        return this._clover_pay(uuid);
    }

    send_payment_cancel(order, uuid) {
        super.send_payment_cancel(order, uuid);
        return this._clover_cancel();
    }

    _clover_pay(uuid) {
        const order = this.pos.get_order();
        const line = order.get_selected_paymentline();

        // if (line.amount < 0) {
        //     this._show_error(_t("Cannot process negative payment amounts."));
        //     return Promise.resolve();
        // }

        const paymentData = this._clover_payment_data(order, line);

        if (line.payment_status !== "force_done" && line.payment_status !== "waitingCard") {
            line.set_payment_status("waitingCapture");
        }

        return this._call_clover(paymentData, "sale")
            .then((response) => this._handle_clover_response(response))
            .then(() => this.handleCloverStatusResponse());
    }

    _clover_payment_data(order, line) {
        return {
            amount_cents: line.amount,
            currency: this.pos.currency?.name || "USD",
            merchant_order_id: line.uuid,
            preferred_payment_method: "card",
            testMode: true,
        };
    }

    _clover_cancel() {
        const order = this.pos.get_order();
        const line = order?.get_selected_paymentline();

        try {
            const message = _t("Payment Cancelled, Please make sure to cancel it from the Clover terminal too");
            if (this.env.services.notification) {
                this.env.services.notification.add(message, { type: "warning", title: _t("Cancel Payment") });
            } else {
                this.env.services.dialog.add(AlertDialog, { title: _t("Cancel Payment"), body: message });
            }
        } catch (error) {
            console.error("Clover: Error showing cancel message:", error);
        }

        if (line) line.set_payment_status("retry");
        return Promise.resolve(true);
    }

    // _call_clover(data, operation) {
    //     console.log("Clover: Sending request to Clover terminal", { data, operation });
    //     return this.pos.data
    //         .silentCall("pos.payment.method", "send_clover_request", [[this.payment_method_id.id], data, operation])
    //         .catch(this._handle_connection_failure.bind(this));
    // }
    _call_clover(data, operation) {
        console.log("Clover: Sending request to Clover terminal", { data, operation });

        // Add POS customer (res.partner) if selected
        const client = this.pos.get_order().get_partner();
        if (client) {
            data.customer_id = client.id;
        }

        // Add POS employee (cashier/user)
        const cashier = this.pos.get_cashier();
        console.log("Clover: Cashier:", cashier.name);
        if (cashier) {
            data.employee_id = cashier.name;
        }

        return this.pos.data
            .silentCall("pos.payment.method", "send_clover_request", [[this.payment_method_id.id], data, operation])
            .catch(this._handle_connection_failure.bind(this));
    }

    _handle_connection_failure(data = {}) {
        const line = this.pending_clover_line();
        if (line) line.set_payment_status("retry");
        this._show_error(_t("Could not connect to the Clover server. Please check your internet connection and try again."));
        return Promise.reject(data);
    }

    pending_clover_line() {
        return this.pos.getPendingPaymentLine("clover");
    }

    async _handle_clover_response(response) {
        const line = this.pending_clover_line();
        if (!line) {
            this._show_error(_t("No pending Clover payment line found."));
            return false;
        }

        if (!response) {
            this._show_error(_t("An error occurred while processing the payment. Please try again."));
            line.set_payment_status("force_done");
            return false;
        }

        if (response.error) {
            this._show_error(_t(response.error.message));
            line.set_payment_status("force_done");
            return false;
        }

        line.set_payment_status("waitingCard");

        return new Promise((resolve) => {
            this.paymentNotificationResolver = resolve;
        });
    }

    async handleCloverStatusResponse() {
        console.log("handleCloverStatusResponse called ---------- ");
        const notification = await this.pos.data.silentCall(
            "pos.payment.method",
            "get_latest_clover_status",
            [[this.payment_method_id.id]]
        );

        const line = this.pending_clover_line();
        if (!line || !notification || !notification.id || !notification.external_id) return false;

        console.log("Clover: Pending payment line:", line);
        console.log("Clover: Received notification:", notification);

        const status = notification.status;
        const transaction_id = notification.id;
        console.log("Clover: Transaction status:", status, "Transaction ID:", transaction_id);

        // if (status === "SUCCESS") {
        //     console.log("Clover: Handling successful transaction");
        //     line.transaction_id = transaction_id;
        //     line.set_payment_status("done");
        //     this.pos.get_order()._compute_payment_summary();
        //     if (this.paymentNotificationResolver) {
        //         this.paymentNotificationResolver(true);
        //         this.paymentNotificationResolver = null;
        //     }
        //     return true;

        if (status === "SUCCESS") {
            console.log("Clover: Handling successful transaction");
            line.transaction_id = transaction_id;
            line.set_payment_status("done");

            const order = this.pos.get_order();
            if (order) {
                try {
                    this.env.services.pos.validatePayment(); // Trigger payment validation
                } catch (error) {
                    console.error("Clover: Failed to validate payment", error);
                    // this._show_error(_t("Failed to finalize the order. Please try again."));
                    return false;
                }
            } else {
                this._show_error(_t("No active order found."));
                return false;
            }

            if (this.paymentNotificationResolver) {
                this.paymentNotificationResolver(true);
                this.paymentNotificationResolver = null;
            }
            return true;

        
        } else if (status === "VOIDED" || status === "REFUNDED") {
            console.log("Clover: Handling voided or refunded transaction");
            line.transaction_id = transaction_id;
            this._show_error(_t(`Transaction has been ${status.toLowerCase()}. Please check the Clover terminal.`));
            line.set_payment_status("reversed");

            if (this.paymentNotificationResolver) {
                this.paymentNotificationResolver(false);
                this.paymentNotificationResolver = null;
            }

            this.env.bus.trigger('clover-payment-failed', { line });
            return false;
        } else {
            console.log("Clover: Transaction status unclear, waiting for more updates");
            line.set_payment_status("waitingCard"); // keep pending
            return false;
        }
    }
}

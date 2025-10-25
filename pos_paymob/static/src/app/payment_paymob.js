/** @odoo-module */

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class PaymentPaymob extends PaymentInterface {
    setup() {
        super.setup(...arguments);
        this.paymentNotificationResolver = null;
    }

    _show_error(msg, title) {
        if (!title) {
            title = _t("Viva Wallet Error");
        }
        this.env.services.dialog.add(AlertDialog, {
            title: title,
            body: msg,
        });
    }

    send_payment_request(uuid) {
        super.send_payment_request(uuid);
        return this._paymob_pay(uuid);
    }

    send_payment_cancel(order, uuid) {     
        super.send_payment_cancel(order, uuid);
        return this._paymob_cancel();
    }

    _paymob_pay(uuid) {
        const order = this.pos.get_order();
        const line = order.get_selected_paymentline();

        if (line.amount < 0) {
            this._show_error(_t("Cannot process negative payment amounts."));
            return Promise.resolve();
        }

        const paymentData = this._paymob_payment_data(order, line);

        // To prevent canceling the payment while the order is being created
        if (line.payment_status !== "force_done" && line.payment_status !== "waitingCard") {
            line.set_payment_status("waitingCapture");
        }
        
        return this._call_paymob(paymentData, 'order').then((response) => {
            return this._handle_paymob_response(response);
        });
    }

    _paymob_payment_data(order, line) {
        const timestamp = new Date().toISOString();
        return {
            amount_cents: line.amount,
            currency: this.pos.currency.name,
            merchant_order_id: `${timestamp}--${order.session_id.id}--${line.uuid}`,
            send_pay_notification_to_terminal_id:line.payment_method_id.id,
            terminal_id: line.payment_method_id.id,
            preferred_payment_method :"card",
            transaction_type:"sale",
            delivery_needed: "false",
        };
    }

    _paymob_cancel() {
        const order = this.pos.get_order();
        if (!order) {
            this._show_error(_t("No active order found to cancel the payment."));
            return Promise.resolve();
        }
        
        const line = order.get_selected_paymentline();
        
        try {
            // Show cancellation message using notification service
            if (this.env.services.notification) {
                this.env.services.notification.add(
                    _t("Payment Cancelled, Please make sure to cancel it from the terminal too"),
                    {
                        type: "warning",
                        title: _t("Cancel Payment"),
                    }
                );
            } else {
                // Fallback to dialog if notification service is not available
                this.env.services.dialog.add(AlertDialog, {
                    title: _t("Cancel Payment"),
                    body: _t("Payment Cancelled, Please make sure to cancel it from the terminal too"),
                });
            }
        } catch (error) {
            console.error("Paymob: Error showing cancel message:", error);
            // Fallback to console log if both methods fail
            console.log("Paymob: Payment Cancelled, Please make sure to cancel it from the terminal too");
        }
        
        // Set payment status to cancelled if line exists
        if (line) {
            line.set_payment_status("retry");
        }
        
        return Promise.resolve(true);
    }
    

    _call_paymob(data, operation) {
        return this.pos.data
            .silentCall("pos.payment.method", "send_paymob_request", [
                [this.payment_method_id.id],
                data,
                operation,
            ])
            .catch(this._handle_connection_failure.bind(this));
    }

    _handle_connection_failure(data = {}) {
        const line = this.pending_paymob_line();
        if (line) {
            line.set_payment_status("retry");
        }
        this._show_error(_t("Could not connect to the Odoo server. Please check your internet connection and try again."));
        
        return Promise.reject(data);
    }
    

    async _handle_paymob_response(response) {
        const line = this.pending_paymob_line();
        if (!line) {
            this._show_error(_t("No pending Paymob payment line found."));
            return false;
        }

        if(!response){
            this._show_error(_t("An error occured while processing the payment, Please try again"));
            line.set_payment_status('force_done');
            return false;
        }

        if (response.error && response.error.status_code === 400) {
            this._show_error(_t(response.error.message));
            line.set_payment_status('force_done');
            return false;
        } else if (response.error) {
            this._show_error(_t(response.error.message));
            line.set_payment_status('force_done');
            return false;
        }


        line.set_payment_status("waitingCard");
        return await new Promise((resolve) => {
            this.paymentNotificationResolver = resolve;
        });
    }

    pending_paymob_line() {
        return this.pos.getPendingPaymentLine("paymob");
    }

    async handlePaymobStatusResponse() {
        const notification = await this.pos.data.silentCall(
            "pos.payment.method",
            "get_latest_paymob_status",
            [[this.payment_method_id.id]]
        );

        const line = this.pending_paymob_line();
        if (!line ) {
            return false;
        }

        if (!notification){
            this._handle_connection_failure();
            return false;
        }

        if (!notification.obj || !notification.obj.order || !notification.obj.order.merchant_order_id){
            return false;
        }

        if (this.pos.get_order().session_id.id !== +notification.obj.order.merchant_order_id.split("--")[1]) {
            return false;
        }
        
        if (line.uuid !== notification.obj.order.merchant_order_id.split("--")[2]) {
            return false;
        }

        const error_occured = notification.obj.error_occured;
        const success = notification.obj.success;
        const is_refunded = notification.obj.is_refunded;
        const is_voided = notification.obj.is_voided;
        const is_void = notification.obj.is_void;
        const refunded_amount = notification.obj.refunded_amount_cents || 0;
        const transaction_id = notification.obj.id;

        console.log("Paymob: Processing transaction status:", {
            success,
            error_occured,
            is_refunded,
            is_voided,
            is_void,
            refunded_amount,
            transaction_id
        });

        // Handle refunded transactions
        if (is_refunded === true) {
            console.log("Paymob: Handling refunded transaction");
            
            // Update transaction details
            line.transaction_id = transaction_id;
            
            // Show refund message
            const refundAmountDisplay = (refunded_amount / 100).toFixed(2);
            this._show_error(`Transaction has been refunded. Amount: ${refundAmountDisplay} ${this.pos.currency.name}`);
            
            // Set payment status to indicate refund
            line.set_payment_status("reversed");
            
            // Create a refund record in the order
            this._handle_refund_transaction(line, refunded_amount, notification.obj);
            
            if (this.paymentNotificationResolver) {
                this.paymentNotificationResolver(false);
            }
            return false;
        }

        // Handle voided transactions
        if (is_voided === true || is_void === true) {
            console.log("Paymob: Handling voided transaction");
            
            // Update transaction details
            line.transaction_id = transaction_id;
            
            this._show_error("Transaction has been voided. Please check the terminal.");
            
            // Set payment status to indicate void
            line.set_payment_status("reversed");
            
            // Handle void transaction
            this._handle_void_transaction(line, notification.obj);
            
            if (this.paymentNotificationResolver) {
                this.paymentNotificationResolver(false);
            }
            return false;
        }

        // Handle error transactions
        if (error_occured === true){
            console.log("Paymob: Handling error transaction");
            this._show_error("An error occurred while processing the payment. Please check the terminal.");
            line.set_payment_status("retry");
            
            if (this.paymentNotificationResolver) {
                this.paymentNotificationResolver(false);
            }
            return false;
        }

        // Handle successful transactions
        if (success === true){
            console.log("Paymob: Handling successful transaction");
            line.transaction_id = transaction_id;
            
            if (notification.obj.source_data){
                line.card_brand = notification.obj.source_data.card_type;
                line.card_no = notification.obj.source_data.pan;
            }
            
            if(notification.obj.data && notification.obj.data.extra_detail){
                line.cardholder_name = notification.obj.data.extra_detail.card_holder_name;
            }
            
            line.set_payment_status("done");
            
            if (this.paymentNotificationResolver) {
                this.paymentNotificationResolver(true);
            }
            return true;
        }

        // Default case - transaction is still pending or in unknown state
        console.log("Paymob: Transaction status unclear, waiting for more updates");
        return false;
    }

    _handle_refund_transaction(original_line, refunded_amount_cents, transaction_obj) {
        console.log("Paymob: Creating refund record");
        
        const order = this.pos.get_order();
        const refund_amount = -(refunded_amount_cents / 100); // Negative amount for refund
        
        try {
            // Add a note to the order about the refund
            const refund_note = `REFUND: Transaction ${transaction_obj.id} refunded ${(refunded_amount_cents / 100).toFixed(2)} ${this.pos.currency.name}`;
            
            // You can add custom logic here to handle the refund
            // For example, create a refund line or update order status
            
            // Store refund information in the payment line
            original_line.refund_amount = refund_amount;
            original_line.refund_transaction_id = transaction_obj.id;
            original_line.is_refunded = true;
            
            console.log("Paymob: Refund handled - Amount:", refund_amount);
            
        } catch (error) {
            console.error("Paymob: Error handling refund:", error);
        }
    }

    _handle_void_transaction(original_line, transaction_obj) {
        console.log("Paymob: Creating void record");
        
        try {
            // Store void information in the payment line
            original_line.is_voided = true;
            original_line.void_transaction_id = transaction_obj.id;
            
            console.log("Paymob: Void handled - Transaction ID:", transaction_obj.id);
            
        } catch (error) {
            console.error("Paymob: Error handling void:", error);
        }
    }

    async _finalize_payment_status(paymentMethod) {
        const result = await this.env.services.orm.searchRead(
            "pos.payment.method",
            [["id", "=", paymentMethod.id]],
            ["paymob_latest_response"]
        );

        if (result && result[0] && result[0].paymob_latest_response) {
            console.log("Paymob: Response found in database");
            
            // Parse the response to check transaction type
            const responseData = JSON.parse(result[0].paymob_latest_response);
            const isRefunded = responseData.obj?.is_refunded;
            const isVoided = responseData.obj?.is_voided || responseData.obj?.is_void;
            
            console.log("Paymob: Transaction data:", responseData);
            console.log("Paymob: Is refunded:", isRefunded);
            console.log("Paymob: Is voided:", isVoided);
            
            const terminal = paymentMethod.payment_terminal;
            if (terminal && terminal.handlePaymobStatusResponse) {
                // Update the payment method
                paymentMethod.paymob_latest_response = result[0].paymob_latest_response;
                
                console.log("Paymob: Calling handlePaymobStatusResponse");
                const handleResult = await terminal.handlePaymobStatusResponse();
                
                // Clear the response after handling
                // Always clear for refunds and voids since they're final states
                if (handleResult !== false || isRefunded || isVoided) {
                    if (this.env.services.orm) {
                        await this.env.services.orm.write(
                            "pos.payment.method",
                            [paymentMethod.id],
                            {"paymob_latest_response": false}
                        );
                    } else {
                        await rpcService("/web/dataset/call_kw", {
                            model: "pos.payment.method",
                            method: "write",
                            args: [[paymentMethod.id], {"paymob_latest_response": false}],
                            kwargs: {},
                        });
                    }
                }
            }
        }
    }
}

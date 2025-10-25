/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        
        // Start polling for Paymob updates
        this._startPaymobPolling();
    },

    _startPaymobPolling() {
        this.paymobPollingInterval = setInterval(() => {
            this._checkPaymobStatus();
        }, 1000); // Check every second
        
        console.log("Paymob: Started polling for updates");
    },

    async _checkPaymobStatus() {
        const paymentLine = this.getPendingPaymentLine("paymob");
        if (!paymentLine) {
            return;
        }

        const paymentMethod = paymentLine.payment_method_id;
        if (!paymentMethod) {
            return;
        }

        try {
            // Try different RPC service access methods
            let rpcService = null;
            
            // Method 1: Try env.services.rpc
            if (this.env.services.rpc) {
                rpcService = this.env.services.rpc;
            }
            // Method 2: Try env.services.orm
            else if (this.env.services.orm) {
                rpcService = this.env.services.orm;
            }
            // Method 3: Try legacy rpc access
            else if (this.rpc) {
                rpcService = this.rpc;
            }
            // Method 4: Use the session rpc
            else if (this.env.session && this.env.session.rpc) {
                rpcService = this.env.session.rpc;
            }

            if (!rpcService) {
                console.error("Paymob: No RPC service found");
                return;
            }

            // Fetch the latest status from the server
            let result;
            
            // Try ORM service first (newer Odoo versions)
            if (this.env.services.orm) {
                result = await this.env.services.orm.read(
                    "pos.payment.method",
                    [paymentMethod.id],
                    ["paymob_latest_response"]
                );
            }
            // Fallback to legacy RPC call
            else {
                result = await rpcService("/web/dataset/call_kw", {
                    model: "pos.payment.method",
                    method: "read",
                    args: [[paymentMethod.id], ["paymob_latest_response"]],
                    kwargs: {},
                });
            }

            if (result && result[0] && result[0].paymob_latest_response) {
                console.log("Paymob: Response found in database");
                
                const terminal = paymentMethod.payment_terminal;
                if (terminal && terminal.handlePaymobStatusResponse) {
                    // Update the payment method
                    paymentMethod.paymob_latest_response = result[0].paymob_latest_response;
                    
                    console.log("Paymob: Calling handlePaymobStatusResponse");
                    terminal.handlePaymobStatusResponse();
                    
                    // Clear the response after handling
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
        } catch (error) {
            console.error("Paymob: Error checking status:", error);
        }
    },

    // Clean up when the store is destroyed
    destroy() {
        if (this.paymobPollingInterval) {
            clearInterval(this.paymobPollingInterval);
        }
        super.destroy();
    },
});
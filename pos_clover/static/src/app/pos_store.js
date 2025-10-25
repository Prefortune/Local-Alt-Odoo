/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this._startCloverPolling();
    },

    _startCloverPolling() {
        this.cloverPollingInterval = setInterval(() => {
            this._checkCloverStatus();
        }, 1000); // Check every second
        console.log("Clover: Started polling for updates");
    },

    async _checkCloverStatus() {
        const paymentLine = this.getPendingPaymentLine("clover");
        if (!paymentLine) {
            return;
        }

        const paymentMethod = paymentLine.payment_method_id;
        if (!paymentMethod) {
            return;
        }

        try {
            let rpcService = this.env.services.orm || this.env.services.rpc || this.rpc || (this.env.session && this.env.session.rpc);
            if (!rpcService) {
                console.error("Clover: No RPC service found");
                return;
            }

            let result;
            if (this.env.services.orm) {
                result = await this.env.services.orm.read(
                    "pos.payment.method",
                    [paymentMethod.id],
                    ["clover_latest_response"]
                );
            } else {
                result = await rpcService("/web/dataset/call_kw", {
                    model: "pos.payment.method",
                    method: "read",
                    args: [[paymentMethod.id], ["clover_latest_response"]],
                    kwargs: {},
                });
            }

            if (result && result[0] && result[0].clover_latest_response) {
                console.log("Clover: Response found in database");
                const terminal = paymentMethod.payment_terminal;
                if (terminal && terminal.handleCloverStatusResponse) {
                    paymentMethod.clover_latest_response = result[0].clover_latest_response;
                    console.log("Clover: Calling handleCloverStatusResponse");
                    terminal.handleCloverStatusResponse();

                    if (this.env.services.orm) {
                        await this.env.services.orm.write(
                            "pos.payment.method",
                            [paymentMethod.id],
                            {"clover_latest_response": false}
                        );
                    } else {
                        await rpcService("/web/dataset/call_kw", {
                            model: "pos.payment.method",
                            method: "write",
                            args: [[paymentMethod.id], {"clover_latest_response": false}],
                            kwargs: {},
                        });
                    }
                }
            }
        } catch (error) {
            console.error("Clover: Error checking status:", error);
        }
    },

    destroy() {
        if (this.cloverPollingInterval) {
            clearInterval(this.cloverPollingInterval);
        }
        super.destroy();
    },
});
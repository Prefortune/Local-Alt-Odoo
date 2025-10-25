/** @odoo-module **/

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

/**
 * Pay4All Payment Interface for Odoo 18
 */
export class Pay4AllPaymentInterface extends PaymentInterface {
    setup() {
        super.setup();
        this.supports_reversals = false;
    }

    /**
     * Handle payment processing
     */
    send_payment_request(cid) {
        return this._pay4all_pay(cid);
    }

    /**
     * Main payment flow
     */
    async _pay4all_pay(cid) {
        const line = this.pos.get_order().get_paymentline(cid);
        const amount = line.get_amount();
        
        try {
            // Show Pay4All payment screens
            await this._showPay4AllScreens(amount, line);
            line.set_payment_status('done');
            return true;
        } catch (error) {
            this._show_error(_t('Payment failed: ') + error.message);
            line.set_payment_status('retry');
            return false;
        }
    }

    /**
     * Show Pay4All payment screens sequence
     */
    async _showPay4AllScreens(amount, line) {
        // This will be implemented with the actual screen components
        console.log('Pay4All payment initiated for amount:', amount);
        
        // Simulate payment processing
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(true);
            }, 2000);
        });
    }

    /**
     * Show error message
     */
    _show_error(msg) {
        this.env.services.notification.add(msg, {
            type: 'danger',
            sticky: false,
        });
    }
}

// Register the payment terminal for Odoo 18
registry.category("payment_interfaces").add("pay4all", Pay4AllPaymentInterface);

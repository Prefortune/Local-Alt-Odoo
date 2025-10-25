/** @odoo-module **/

import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";

/**
 * Pay4All Payment Interface for Odoo 16
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
            return true;
        } catch (error) {
            this._show_error(_t('Payment failed: ') + error.message);
            return false;
        }
    }

    /**
     * Show Pay4All payment screens sequence
     */
    async _showPay4AllScreens(amount, line) {
        // This will be implemented with the actual screen components
        console.log('Pay4All payment initiated for amount:', amount);
        
        // For now, simulate successful payment
        line.set_payment_status('done');
        return true;
    }

    /**
     * Show error message
     */
    _show_error(msg) {
        this.pos.env.services.notification.add(msg, {
            type: 'danger',
            sticky: false,
        });
    }
}

// Register the payment interface
const { PaymentTerminal } = require('point_of_sale.models');

PaymentTerminal.prototype.payment_interface_factory = function() {
    if (this.use_payment_terminal === 'pay4all') {
        return new Pay4AllPaymentInterface(this);
    }
    return this._super(...arguments);
};
        
        if (digits.startsWith('+244')) {
            const phoneDigits = digits.substring(4);
            let formatted = '+244';
            
            if (phoneDigits.length > 0) {
                formatted += ' ' + phoneDigits.substring(0, 3);
                if (phoneDigits.length > 3) {
                    formatted += ' ' + phoneDigits.substring(3, 6);
                    if (phoneDigits.length > 6) {
                        formatted += ' ' + phoneDigits.substring(6, 9);
                    }
                }
            }
            return formatted;
        }
        
        return digits;
    }

    validatePhone() {
        const phone = this.state.phoneNumber.trim();
        this.state.phoneError = null;
        
        if (!phone) return false;
        
        const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
        const patterns = [
            /^\+244[9][0-9]{8}$/,
            /^244[9][0-9]{8}$/,
            /^[9][0-9]{8}$/
        ];
        
        const isValid = patterns.some(pattern => pattern.test(cleanPhone));
        
        if (!isValid && phone.length > 3) {
            this.state.phoneError = 'Número de telefone inválido. Use formato: +244 9XX XXX XXX';
            return false;
        }
        
        return isValid;
    }

    canContinue() {
        return this.state.selectedMethod && 
               this.validatePhone() && 
               !this.state.isProcessing;
    }

    async continuePayment() {
        if (!this.canContinue()) return;

        this.state.isProcessing = true;
        
        try {
            const paymentData = {
                method: this.state.selectedMethod,
                phone: this.state.phoneNumber.replace(/\D/g, ''),
                amount: this.props.amount,
                currency: this.props.currency,
                order_id: this.props.order_id,
                description: this.props.description
            };

            this.confirm(paymentData);
            
        } catch (error) {
            console.error('Erro ao processar pagamento:', error);
            this.state.phoneError = 'Erro ao processar. Tente novamente.';
        } finally {
            this.state.isProcessing = false;
        }
    }

    cancel() {
        super.cancel();
    }
}

Pay4AllPaymentScreen.template = 'Pay4AllPaymentScreen';

/**
 * Pay4All Payment Interface
 */
class Pay4AllPaymentInterface extends PaymentInterface.PaymentInterface {
    constructor() {
        super(...arguments);
        this.supports_reversals = false;
    }

    async send_payment_request(cid) {
        const line = this.pos.get_order().selected_paymentline;
        const order = this.pos.get_order();
        
        const paymentData = {
            amount: line.amount,
            currency: this.pos.currency.name,
            order_id: order.name || 'POS-' + Date.now(),
            description: this._getPaymentDescription(order)
        };

        try {
            const result = await this.showPopup('Pay4AllPaymentScreen', {
                title: 'Pay4All Payment',
                ...paymentData
            });

            if (result.confirmed && result.payload) {
                line.set_payment_status('waitingCard');
                
                setTimeout(() => {
                    line.set_payment_status('done');
                    line.can_be_reversed = false;
                }, 1000);
                
                return true;
            } else {
                line.set_payment_status('retry');
                return false;
            }
            
        } catch (error) {
            console.error('Erro no pagamento Pay4All:', error);
            line.set_payment_status('force_done');
            return false;
        }
    }

    _getPaymentDescription(order) {
        const orderlines = order.get_orderlines();
        if (orderlines.length === 1) {
            const line = orderlines[0];
            return `${line.product.display_name} - ${line.quantity}x${line.price} Kz`;
        } else {
            return `Pedido ${order.name} - ${orderlines.length} itens`;
        }
    }

    send_payment_cancel(order, cid) {
        return Promise.resolve(false);
    }
}

// Registrar componentes
Gui.Gui.registerComponent(Pay4AllPaymentScreen);
PaymentInterface.PaymentInterface.register('pay4all', Pay4AllPaymentInterface);

return {
    Pay4AllPaymentScreen,
    Pay4AllPaymentInterface
};

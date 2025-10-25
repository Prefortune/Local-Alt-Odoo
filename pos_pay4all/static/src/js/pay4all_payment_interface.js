/** @odoo-module **/

const { PaymentInterface } = require('point_of_sale.PaymentInterface');

/**
 * Pay4All Payment Interface
 * Integra o Pay4All com o sistema de pagamentos do POS
 */
export class Pay4AllPaymentInterface extends PaymentInterface {
    
    setup() {
        super.setup();
        this.supports_reversals = false;
    }

    /**
     * Inicia o processo de pagamento Pay4All
     */
    async send_payment_request(cid) {
        const line = this.pos.get_order().selected_paymentline;
        const order = this.pos.get_order();
        
        // Dados do pagamento
        const paymentData = {
            amount: line.amount,
            currency: this.pos.currency.name,
            order_id: order.name || 'POS-' + Date.now(),
            description: this._getPaymentDescription(order)
        };

        try {
            // Etapa 1: Abre a Tela 1 - Seleção de Método
            const result = await this.pos.env.services.popup.add('Pay4AllPaymentScreen', {
                title: 'Pay4All Payment',
                ...paymentData
            });

            if (result.confirmed && result.payload) {
                const { nextScreen, data } = result.payload;
                
                if (nextScreen === 'processing') {
                    // Etapa 2: Abre a Tela 2 - Processamento
                    return await this.handleProcessingScreen(line, data);
                }
            } else {
                // Cancelado pelo usuário na Tela 1
                line.set_payment_status('retry');
                return false;
            }
            
        } catch (error) {
            console.error('Erro no pagamento Pay4All:', error);
            line.set_payment_status('force_done');
            return false;
        }
    }

    /**
     * Gerencia a Tela 2 - Processamento
     */
    async handleProcessingScreen(line, paymentData) {
        try {
            line.set_payment_status('waitingCard');
            
            // Abre Tela 2 - Processamento
            const result = await this.pos.env.services.popup.add('Pay4AllProcessingScreen', {
                title: 'Pay4All Processing',
                ...paymentData
            });

            if (result.confirmed && result.payload) {
                const { success, error, reference, nextScreen, data } = result.payload;
                
                if (success) {
                    // Pagamento bem-sucedido
                    line.set_payment_status('done');
                    line.can_be_reversed = false;
                    line.transaction_id = reference;
                    return true;
                } else if (nextScreen === 'multicaixa_wait') {
                    // Transicionar para Tela 3 - Aguardo Multicaixa
                    return await this.handleMulticaixaWaitScreen(line, data);
                } else {
                    // Erro ou timeout
                    console.error('Erro no pagamento:', error);
                    line.set_payment_status('force_done');
                    return false;
                }
            } else {
                // Cancelado na Tela 2
                line.set_payment_status('retry');
                return false;
            }
            
        } catch (error) {
            console.error('Erro na Tela 2:', error);
            line.set_payment_status('force_done');
            return false;
        }
    }

    /**
     * Gerencia a Tela 3 - Aguardo Multicaixa
     */
    async handleMulticaixaWaitScreen(line, paymentData) {
        try {
            // Abre Tela 3 - Aguardo Multicaixa
            const result = await this.pos.env.services.popup.add('Pay4AllMulticaixaWaitScreen', {
                title: 'Pay4All Multicaixa Wait',
                ...paymentData
            });

            if (result.confirmed && result.payload) {
                const { success, error, reference } = result.payload;
                
                if (success) {
                    // Pagamento Multicaixa bem-sucedido
                    line.set_payment_status('done');
                    line.can_be_reversed = false;
                    line.transaction_id = reference;
                    return true;
                } else {
                    // Erro ou timeout no Multicaixa
                    console.error('Erro no Multicaixa:', error);
                    line.set_payment_status('force_done');
                    return false;
                }
            } else {
                // Cancelado na Tela 3
                line.set_payment_status('retry');
                return false;
            }
            
        } catch (error) {
            console.error('Erro na Tela 3:', error);
            line.set_payment_status('force_done');
            return false;
        }
    }

    /**
     * Gera descrição do pagamento baseada no pedido
     */
    _getPaymentDescription(order) {
        const orderlines = order.get_orderlines();
        if (orderlines.length === 1) {
            const line = orderlines[0];
            return `${line.product.display_name} - ${line.quantity}x${line.price} Kz`;
        } else {
            return `Pedido ${order.name} - ${orderlines.length} itens`;
        }
    }

    /**
     * Não implementado - Pay4All não suporta reversão
     */
    send_payment_cancel(order, cid) {
        return Promise.resolve(false);
    }

    /**
     * Verifica status do pagamento (para implementar later)
     */
    async check_payment_status() {
        // Implementar verificação de status via API
        return true;
    }
}

// Registrar a interface de pagamento
PaymentInterface.register('pay4all', Pay4AllPaymentInterface);

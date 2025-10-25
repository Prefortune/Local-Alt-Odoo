/** @odoo-module **/

import { AbstractAwaitablePopup } from 'point_of_sale.popups';
import { useState } from '@odoo/owl';

/**
 * Pay4All Multicaixa Wait Screen - Tela 3: Aguardo Multicaixa
 * Tela específica para aguardar confirmação do Multicaixa Express
 */
export class Pay4AllMulticaixaWaitScreen extends AbstractAwaitablePopup {
    static template = 'Pay4AllMulticaixaWaitScreen';
    
    setup() {
        super.setup();
        
        // Estado reativo da tela
        this.state = useState({
            reference: this.generateReference(),
            isWaiting: true,
            paymentStatus: 'pending'
        });
        
        // Configurações
        this.API_CHECK_INTERVAL = 3000; // 3 segundos (mais frequente para Multicaixa)
        this.MAX_WAIT_TIME = 300000; // 5 minutos máximo
        
        // Iniciar processo
        this.startMulticaixaProcess();
    }

    /**
     * Inicia o processo específico do Multicaixa
     */
    async startMulticaixaProcess() {
        try {
            // 1. Fazer request para API Multicaixa
            const paymentRequest = await this.makeMulticaixaRequest();
            
            if (paymentRequest.success) {
                this.state.reference = paymentRequest.reference;
                
                // 2. Iniciar verificação contínua de status
                this.startStatusCheck();
                
                // 3. Timeout máximo
                this.startMaxTimeout();
            } else {
                throw new Error('Falha ao iniciar pagamento Multicaixa');
            }
            
        } catch (error) {
            console.error('Erro ao processar Multicaixa:', error);
            this.handlePaymentError(error);
        }
    }

    /**
     * Faz request específico para API Multicaixa
     */
    async makeMulticaixaRequest() {
        const payload = {
            api_key: "8UmVR3yf7HwBMkNbs6DTDIYdGpOWr7hXVthaqMo30BXSu4WL",
            account_number: "00375967",
            amount: parseFloat(this.props.amount),
            description: this.props.description,
            order_id: this.props.order_id,
            customer_phone: this.props.phone.replace(/\D/g, ''),
            payment_method: 'multicaixa_express',
            callback_url: `${window.location.origin}/pay4all/callback`
        };
        
        try {
            const response = await fetch('https://payment.momenu.space/payment/appy/request/plugin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                return {
                    success: true,
                    reference: data.reference || this.state.reference,
                    transaction_id: data.transaction_id
                };
            } else {
                throw new Error(data.message || 'Erro na API Multicaixa');
            }
            
        } catch (error) {
            console.error('Erro na API Multicaixa:', error);
            
            // Simular sucesso para teste (remover em produção)
            return {
                success: true,
                reference: this.state.reference,
                transaction_id: 'MCX-' + Date.now()
            };
        }
    }

    /**
     * Inicia verificação mais frequente para Multicaixa
     */
    startStatusCheck() {
        this.statusTimer = setInterval(async () => {
            try {
                const status = await this.checkMulticaixaStatus();
                
                if (status.completed) {
                    this.handlePaymentSuccess(status);
                } else if (status.failed) {
                    this.handlePaymentError(status);
                }
                
            } catch (error) {
                console.error('Erro ao verificar status Multicaixa:', error);
            }
        }, this.API_CHECK_INTERVAL);
    }

    /**
     * Timeout máximo para Multicaixa (5 minutos)
     */
    startMaxTimeout() {
        this.maxTimer = setTimeout(() => {
            this.handleTimeout();
        }, this.MAX_WAIT_TIME);
    }

    /**
     * Verifica status específico do Multicaixa
     */
    async checkMulticaixaStatus() {
        try {
            const response = await fetch('https://payment.momenu.space/payment/status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    api_key: "8UmVR3yf7HwBMkNbs6DTDIYdGpOWr7hXVthaqMo30BXSu4WL",
                    reference: this.state.reference,
                    payment_method: 'multicaixa_express'
                })
            });
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            console.error('Erro ao verificar status Multicaixa:', error);
            return { completed: false, failed: false };
        }
    }

    /**
     * Gera referência única para Multicaixa
     */
    generateReference() {
        return 'MCX' + Math.floor(100000000 + Math.random() * 900000000).toString();
    }

    /**
     * Manipula sucesso do pagamento
     */
    handlePaymentSuccess(status) {
        this.clearTimers();
        this.state.paymentStatus = 'success';
        
        // Resolve com sucesso
        this.confirm({
            success: true,
            reference: this.state.reference,
            method: 'multicaixa',
            ...status
        });
    }

    /**
     * Manipula erro no pagamento
     */
    handlePaymentError(error) {
        this.clearTimers();
        this.state.paymentStatus = 'failed';
        
        // Resolve com erro
        this.confirm({
            success: false,
            error: error.message || 'Erro no pagamento Multicaixa',
            method: 'multicaixa'
        });
    }

    /**
     * Manipula timeout máximo
     */
    handleTimeout() {
        this.clearTimers();
        this.state.paymentStatus = 'timeout';
        
        // Resolve com timeout
        this.confirm({
            success: false,
            error: 'Timeout - Multicaixa não confirmado em 5 minutos',
            method: 'multicaixa'
        });
    }

    /**
     * Limpa todos os timers
     */
    clearTimers() {
        if (this.statusTimer) {
            clearInterval(this.statusTimer);
        }
        if (this.maxTimer) {
            clearTimeout(this.maxTimer);
        }
    }

    /**
     * Cancela o pagamento
     */
    cancel() {
        this.clearTimers();
        super.cancel();
    }

    /**
     * Cleanup ao destruir componente
     */
    willUnmount() {
        this.clearTimers();
    }
}

/** @odoo-module **/

import { AbstractAwaitablePopup } from 'point_of_sale.popups';
import { useState } from '@odoo/owl';

/**
 * Pay4All Processing Screen - Tela 2: Processamento/Aguardo
 * Implementa countdown de 90 segundos e integração com API
 */
export class Pay4AllProcessingScreen extends AbstractAwaitablePopup {
    static template = 'Pay4AllProcessingScreen';
    
    setup() {
        super.setup();
        
        // Estado reativo da tela
        this.state = useState({
            timeRemaining: 90,          // 90 segundos de timeout
            reference: this.generateReference(),
            isProcessing: true,
            paymentStatus: 'pending',   // pending, success, failed, timeout
            progressPercentage: 100
        });
        
        // Configurações
        this.TOTAL_TIME = 90; // 90 segundos
        this.API_CHECK_INTERVAL = 5000; // 5 segundos
        this.COUNTDOWN_INTERVAL = 1000; // 1 segundo
        
        // Iniciar processo
        this.startPaymentProcess();
    }

    /**
     * Inicia o processo de pagamento
     */
    async startPaymentProcess() {
        try {
            // 1. Fazer request para API Pay4All
            const paymentRequest = await this.makePaymentRequest();
            
            if (paymentRequest.success) {
                this.state.reference = paymentRequest.reference;
                
                // 2. Iniciar countdown
                this.startCountdown();
                
                // 3. Iniciar verificação de status
                this.startStatusCheck();
            } else {
                throw new Error('Falha ao iniciar pagamento');
            }
            
        } catch (error) {
            console.error('Erro ao processar pagamento:', error);
            this.handlePaymentError(error);
        }
    }

    /**
     * Faz request para API Pay4All
     */
    async makePaymentRequest() {
        const apiUrl = this.getApiUrl();
        const payload = this.buildPaymentPayload();
        
        try {
            const response = await fetch(apiUrl, {
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
                throw new Error(data.message || 'Erro na API');
            }
            
        } catch (error) {
            console.error('Erro na API Pay4All:', error);
            
            // Simular sucesso para teste (remover em produção)
            return {
                success: true,
                reference: this.state.reference,
                transaction_id: 'TEST-' + Date.now()
            };
        }
    }

    /**
     * Retorna URL da API baseada no método
     */
    getApiUrl() {
        const baseUrl = 'https://payment.momenu.space/payment';
        
        switch (this.props.method) {
            case 'ekwanza':
                return `${baseUrl}/ekwanza/request/plugin`;
            case 'multicaixa':
                return `${baseUrl}/appy/request/plugin`;
            default:
                throw new Error('Método de pagamento inválido');
        }
    }

    /**
     * Constrói payload para API
     */
    buildPaymentPayload() {
        return {
            api_key: "8UmVR3yf7HwBMkNbs6DTDIYdGpOWr7hXVthaqMo30BXSu4WL",
            account_number: "00375967",
            amount: parseFloat(this.props.amount),
            description: this.props.description,
            order_id: this.props.order_id,
            customer_phone: this.props.phone.replace(/\D/g, ''),
            payment_method: this.props.method === 'ekwanza' ? 'ekwanza' : 'multicaixa_express',
            callback_url: `${window.location.origin}/pay4all/callback`
        };
    }

    /**
     * Inicia o countdown de 90 segundos
     */
    startCountdown() {
        this.countdownTimer = setInterval(() => {
            this.state.timeRemaining--;
            this.updateProgress();
            
            // Adicionar classe de aviso nos últimos 15 segundos
            if (this.state.timeRemaining <= 15) {
                this.addWarningClass();
            }
            
            // Timeout atingido
            if (this.state.timeRemaining <= 0) {
                this.handleTimeout();
            }
        }, this.COUNTDOWN_INTERVAL);
    }

    /**
     * Inicia verificação periódica de status
     */
    startStatusCheck() {
        this.statusTimer = setInterval(async () => {
            try {
                const status = await this.checkPaymentStatus();
                
                if (status.completed) {
                    this.handlePaymentSuccess(status);
                } else if (status.failed) {
                    this.handlePaymentError(status);
                }
                
            } catch (error) {
                console.error('Erro ao verificar status:', error);
            }
        }, this.API_CHECK_INTERVAL);
    }

    /**
     * Verifica status do pagamento via API
     */
    async checkPaymentStatus() {
        try {
            const response = await fetch('https://payment.momenu.space/payment/status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    api_key: "8UmVR3yf7HwBMkNbs6DTDIYdGpOWr7hXVthaqMo30BXSu4WL",
                    reference: this.state.reference
                })
            });
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            console.error('Erro ao verificar status:', error);
            return { completed: false, failed: false };
        }
    }

    /**
     * Atualiza progress bar baseado no tempo restante
     */
    updateProgress() {
        const percentage = (this.state.timeRemaining / this.TOTAL_TIME) * 100;
        this.state.progressPercentage = Math.max(0, percentage);
    }

    /**
     * Adiciona classes de aviso para countdown
     */
    addWarningClass() {
        const countdownEl = document.querySelector('.pay4all-countdown');
        const progressEl = document.querySelector('.pay4all-progress-fill');
        
        if (countdownEl) {
            countdownEl.classList.add('warning');
        }
        
        if (progressEl) {
            if (this.state.timeRemaining <= 5) {
                progressEl.classList.add('critical');
            } else {
                progressEl.classList.add('warning');
            }
        }
    }

    /**
     * Formata tempo para exibição (M:SS)
     */
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    /**
     * Retorna porcentagem da progress bar
     */
    getProgressPercentage() {
        return this.state.progressPercentage;
    }

    /**
     * Gera referência única para o pagamento
     */
    generateReference() {
        return Math.floor(100000000 + Math.random() * 900000000).toString();
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
            error: error.message || 'Erro no pagamento'
        });
    }

    /**
     * Manipula timeout
     */
    handleTimeout() {
        this.clearTimers();
        this.state.paymentStatus = 'timeout';
        
        // Se for Multicaixa, transicionar para Tela 3
        if (this.props.method === 'multicaixa') {
            this.confirm({
                success: false,
                nextScreen: 'multicaixa_wait',
                data: this.props
            });
        } else {
            // Para e-Kwanza, resolver com timeout
            this.confirm({
                success: false,
                error: 'Timeout - Pagamento não confirmado em 90 segundos'
            });
        }
    }

    /**
     * Limpa todos os timers
     */
    clearTimers() {
        if (this.countdownTimer) {
            clearInterval(this.countdownTimer);
        }
        if (this.statusTimer) {
            clearInterval(this.statusTimer);
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

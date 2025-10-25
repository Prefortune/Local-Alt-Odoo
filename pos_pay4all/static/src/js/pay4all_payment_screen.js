/** @odoo-module **/

import { AbstractAwaitablePopup } from 'point_of_sale.popups';
import { _lt } from 'web.core';
import { useState } from '@odoo/owl';

/**
 * Pay4All Payment Screen - Tela 1: Seleção de Método
 * Replica exatamente o design dos mockups fornecidos
 */
export class Pay4AllPaymentScreen extends AbstractAwaitablePopup {
    static template = 'Pay4AllPaymentScreen';
    
    setup() {
        super.setup();
        
        // Estado reativo da tela
        this.state = useState({
            selectedMethod: null,       // 'ekwanza' ou 'multicaixa'
            phoneNumber: '',           // Número de telefone do cliente
            phoneError: null,          // Mensagem de erro para validação
            isProcessing: false        // Estado de processamento
        });
    }

    /**
     * Seleciona o método de pagamento (e-Kwanza ou Multicaixa Express)
     */
    selectMethod(method) {
        this.state.selectedMethod = method;
        this.state.phoneError = null;
        
        // Foca no campo de telefone após seleção
        setTimeout(() => {
            const phoneInput = document.getElementById('pay4all-phone');
            if (phoneInput) {
                phoneInput.focus();
            }
        }, 100);
    }

    /**
     * Valida o número de telefone angolano
     * Formatos aceitos: +244XXXXXXXXX, 244XXXXXXXXX, 9XXXXXXXX
     */
    validatePhone() {
        const phone = this.state.phoneNumber.trim();
        this.state.phoneError = null;
        
        if (!phone) {
            return false;
        }
        
        // Remove espaços e caracteres especiais
        const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
        
        // Padrões válidos para Angola
        const patterns = [
            /^\+244[9][0-9]{8}$/,      // +244xxxxxxxxx
            /^244[9][0-9]{8}$/,        // 244xxxxxxxxx  
            /^[9][0-9]{8}$/            // 9xxxxxxxx
        ];
        
        const isValid = patterns.some(pattern => pattern.test(cleanPhone));
        
        if (!isValid && phone.length > 3) {
            this.state.phoneError = 'Número de telefone inválido. Use formato: +244 9XX XXX XXX';
            return false;
        }
        
        return isValid;
    }

    /**
     * Manipula a entrada de telefone com formatação automática
     */
    onPhoneInput(event) {
        const value = event.target.value;
        this.state.phoneNumber = this.formatPhoneNumber(value);
        this.validatePhone();
    }

    /**
     * Formata o número de telefone para exibição
     */
    formatPhoneNumber(value) {
        // Remove tudo que não é dígito
        let digits = value.replace(/\D/g, '');
        
        // Se começar com 244, adiciona o +
        if (digits.startsWith('244')) {
            digits = '+244' + digits.substring(3);
        }
        // Se começar com 9 e tiver 9 dígitos, adiciona +244
        else if (digits.startsWith('9') && digits.length >= 9) {
            digits = '+244' + digits;
        }
        // Se não tiver prefixo e tiver mais de 9 dígitos, assume +244
        else if (!digits.startsWith('+') && digits.length > 9) {
            digits = '+244' + digits.substring(digits.length - 9);
        }
        
        // Formatação visual: +244 9XX XXX XXX
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

    /**
     * Verifica se pode continuar (método selecionado + telefone válido)
     */
    canContinue() {
        return this.state.selectedMethod && 
               this.validatePhone() && 
               !this.state.isProcessing;
    }

    /**
     * Continua para a próxima tela (processamento)
     */
    async continuePayment() {
        if (!this.canContinue()) {
            return;
        }

        this.state.isProcessing = true;
        
        try {
            // Dados para próxima tela
            const paymentData = {
                method: this.state.selectedMethod,
                phone: this.state.phoneNumber, // Manter formatação para exibição
                amount: this.props.amount,
                currency: this.props.currency,
                order_id: this.props.order_id,
                description: this.props.description
            };

            // Resolve com os dados indicando próxima tela
            this.confirm({
                nextScreen: 'processing',
                data: paymentData
            });
            
        } catch (error) {
            console.error('Erro ao processar pagamento:', error);
            this.state.phoneError = 'Erro ao processar. Tente novamente.';
        } finally {
            this.state.isProcessing = false;
        }
    }

    /**
     * Cancela o pagamento e fecha a tela
     */
    cancel() {
        super.cancel();
    }

    /**
     * Retorna o título baseado no método selecionado
     */
    getSelectedMethodTitle() {
        switch (this.state.selectedMethod) {
            case 'ekwanza':
                return 'E-kwanza';
            case 'multicaixa':
                return 'Multicaixa Express';
            default:
                return '';
        }
    }
}

// Registrar o componente
Pay4AllPaymentScreen.template = 'Pay4AllPaymentScreen';

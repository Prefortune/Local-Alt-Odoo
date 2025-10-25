/** @odoo-module **/

const { Gui } = require('point_of_sale.Gui');
const { PaymentInterface } = require('point_of_sale.PaymentInterface');

import { Pay4AllPaymentScreen } from './pay4all_payment_screen';
import { Pay4AllProcessingScreen } from './pay4all_processing_screen';
import { Pay4AllMulticaixaWaitScreen } from './pay4all_multicaixa_wait_screen';
import { Pay4AllPaymentInterface } from './pay4all_payment_interface';

// Registrar todos os componentes para o POS
Gui.registerComponent(Pay4AllPaymentScreen);
Gui.registerComponent(Pay4AllProcessingScreen);
Gui.registerComponent(Pay4AllMulticaixaWaitScreen);

// Registrar a interface de pagamento
PaymentInterface.register('pay4all', Pay4AllPaymentInterface);

// Exportar para uso em outros módulos
export { 
    Pay4AllPaymentScreen, 
    Pay4AllProcessingScreen, 
    Pay4AllMulticaixaWaitScreen,
    Pay4AllPaymentInterface 
};

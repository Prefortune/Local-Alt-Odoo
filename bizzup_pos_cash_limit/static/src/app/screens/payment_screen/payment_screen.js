/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ask } from "@point_of_sale/app/store/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";


patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.orm = useService('orm');
    },
    async validateOrder(isForceValidate) {
        const posCashLimit = await this.orm.call('res.config.settings', "get_pos_cash_payment_limit", []);

        const totalCashAmount = this.paymentLines.reduce((total, line) => {
            return line.payment_method_id?.is_cash_method ? total + line.get_amount() : total;
        }, 0);
        const totalAmount = this.currentOrder.get_total_with_tax()
        if (posCashLimit > 0 && totalAmount > posCashLimit){
            if (totalCashAmount > posCashLimit || totalCashAmount > (totalAmount * 0.1)) {
                const limitToShow = totalCashAmount > posCashLimit ? posCashLimit : totalAmount * 0.1;
                console.log('validateOrder');
                await ask(this.dialog, {
                    title: _t('Alert'),
                    body: _t(
                        "אינך יכול לשלם סכום כזה במזומן. נסה או סכום מתחת ל%s, או סכום הקטן מעשרה אחוז מסך העסקה, הנמוך מביניהם!",
                        limitToShow
                    ),
                });
                return;
            }
        }


        await super.validateOrder(isForceValidate);
    },
});





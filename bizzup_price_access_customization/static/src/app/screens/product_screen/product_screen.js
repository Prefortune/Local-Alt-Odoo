import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.pos = usePos();
        this.dialog = useService("dialog");
    },

    async onNumpadClick(buttonValue) {

        if (buttonValue == 'price') {

            console.log("this",this)
            const selectedOrderlineProductID = this.pos.get_order().get_selected_orderline().product_id.id;

            // Call the server-side method
            const datas = await this.orm.call('pos.session', 'get_created_user_of_product', [selectedOrderlineProductID], {
                product: selectedOrderlineProductID,
            });

            // Ensure datas is either 'false' (string) or false (boolean)
            if (datas === false || datas === 'false') {

                // Show the confirmation dialog if the condition is true
                this.dialog.add(ConfirmationDialog, {
                    title: _t('Unit Price'),
                    body: _t(' שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך'),
                });
                return;
            }
        }

        const result = super.onNumpadClick(buttonValue);
        return result;
    },
});

/** @odoo-module */

import { OpeningControlPopup } from "@point_of_sale/app/store/opening_control_popup/opening_control_popup";
import {patch} from "@web/core/utils/patch";
import {useState} from "@odoo/owl";

patch(OpeningControlPopup.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            notes: "",
            openingCash: this.env.utils.formatCurrency(
                this.pos.session.cash_register_balance_start || 0,
                false
            ),
        });
    },
    async confirm() {
        await super.confirm();
    }, handleInputValid() {
        return false;
    },
    openDetailsPopup() {
        return false;
    },
    getValue() {
        return this.pos.session.cash_register_balance_start;
    }
});
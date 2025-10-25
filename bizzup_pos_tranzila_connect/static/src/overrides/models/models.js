/** @odoo-module **/

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(PosOrder.prototype, {
    // new_limit to pos payment receipt
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        result.new_limit = this.selected_limit;
        result.new_npay = this.selected_npay;
        return result;
    },
});

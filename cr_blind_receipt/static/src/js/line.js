/** @odoo-module **/

import LineComponent from "@stock_barcode/components/line";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { useState } from "@odoo/owl";

patch(LineComponent.prototype, {
    setup() {
        super.setup?.();

        this.state = useState({
            blind_receipt: false,
            is_loading: true,
        });


        this.loadBlindReceiptStatus();
    },
    get componentClasses() {
            return [
                this.isComplete ? 'o_line_not_completed' : 'o_line_not_completed',
                this.isSelected ? 'o_selected o_highlight' : ''
            ].join(' ');
        },
    async loadBlindReceiptStatus() {
        const recordId = this.env?.model?.record?.id;
        if (recordId) {
            const res = await rpc("/web/dataset/call_kw", {
                model: "stock.picking.type",
                method: "can_show_blind_receipt",
                args: [recordId],
                kwargs: {},
            });

            this.state.blind_receipt = res === true;
        }
        this.state.is_loading = false;
    },
});
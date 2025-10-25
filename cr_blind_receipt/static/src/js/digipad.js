import { Digipad } from '@stock_barcode/widgets/digipad';
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { useState } from "@odoo/owl";

patch(Digipad.prototype, {
    setup() {
        super.setup?.();

        this.state.blind_receipt = false;

        this.loadBlindReceiptStatus();
    },
    async loadBlindReceiptStatus() {
        console.log('record from digipad ',this.props.record.data.picking_id[0])
            const recordId = this.props?.record?.data?.picking_id[0];
            if (recordId) {
                const res = await rpc("/web/dataset/call_kw", {
                    model: "stock.picking.type",
                    method: "can_show_blind_receipt",
                    args: [recordId],
                    kwargs: {},
                });


                this.state.blind_receipt = res === true;
            }
        },
 });
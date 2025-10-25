/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import BarcodePickingModel from '@stock_barcode/models/barcode_picking_model';
import { rpc } from "@web/core/network/rpc";

patch(BarcodePickingModel.prototype, {

    get shouldOpenSignatureModal() {
        const { picking_type_code: pickingTypeCode, signature } = this.record;
        let canOpen = false;
        try {
            const result = rpc("/web/dataset/call_kw", {
                model: this.resModel,
                method: "can_show_signature_modal",
                args: [[this.resId]],
                kwargs: {},
            });
            canOpen = result === true;
        } catch (error) {
            console.warn('Failed to fetch backend condition:', error);
        }
        return pickingTypeCode === 'outgoing' && !signature && this.groups.group_stock_sign_delivery && canOpen;
    },

});
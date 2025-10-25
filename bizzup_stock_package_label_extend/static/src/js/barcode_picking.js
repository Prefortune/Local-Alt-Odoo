/** @odoo-module **/

import BarcodePickingModel from '@stock_barcode/models/barcode_picking_model';
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

console.log("🔧 Patching BarcodePickingModel");

patch(BarcodePickingModel.prototype, {
    get printButtons() {
        console.log("✅ Overridden printButtons method called!");

        const buttons = [
            {
                name: _t("Print Picking Operations"),
                class: 'o_print_picking',
                method: 'do_print_picking',
            }, {
                name: _t("Print Delivery Slip"),
                class: 'o_print_delivery_slip',
                method: 'action_print_delivery_slip',
            }, {
                name: _t("Print Barcodes"),
                class: 'o_print_barcodes',
                method: 'action_print_barcode',
            }, {
                name: _t("Picking Barcode"),
                class: 'o_print_picking_barcodes',
                method: 'action_print_picking_barcode',
            },
        ];
        if (this.groups.group_tracking_lot) {
            buttons.push({
                name: _t("Print Packages"),
                class: 'o_print_packages',
                method: 'action_print_packges',
            });
        }
        return buttons;
    },
});

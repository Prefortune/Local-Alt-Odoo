/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { BasePrinter } from "@point_of_sale/app/printer/base_printer";
import { patch } from "@web/core/utils/patch";
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { useRef, onMounted } from "@odoo/owl";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { WaComposerPopup } from "@tus_meta_wa_pos/js/Popups/pos_wa_composer";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
    },
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.templates = loadedData['wa.template'];
        this.loadwatemplates();
        this.providers = loadedData['provider'];
        this.loadProviders();
    },
    async loadwatemplates() {
        let watemplates = await this.orm.call("wa.template", "search_read", []);
        this.templates = watemplates;
    },
    async loadProviders() {
        let providers = await this.orm.call('provider', 'search_read', []);
        this.providers = providers;
    }

});
patch(ReceiptScreen.prototype, {
    /**
     * @override
     */
    setup() {
        super.setup();
        onMounted(() => {
            // Here, we send a task to the event loop that handles
            // the printing of the receipt when the component is mounted.
            // We are doing this because we want the receipt screen to be
            // displayed regardless of what happen to the handleAutoPrint
            // call.
            var self = this
            this.env.services.user.hasGroup('tus_meta_wa_pos.whatsapp_group_pos_user').then(async function (has_group) {
                if (has_group) {
                    $(self.el).find('.send_by_whatsapp').show();
                    const order = self.currentOrder;
                    const client = order.get_partner();
                    if (self.pos.config.send_pos_receipt_on_validate && self.pos.config.template_id && client.mobile) {
                        const printer = new BasePrinter(null, self.env.pos);
                        const receiptString = $('.pos-receipt-container').length && $('.pos-receipt-container')[0].innerHTML;
                        const ticketImage1 = await html2canvas($('.pos-receipt-container')[0], { addClass: "pos-receipt-print" });
                        const ticketImage = ticketImage1.toDataURL("image/png");
                        const orderName = order.get_name();
                        await self.env.services.rpc("/send/receipt", {
                            'provider': self.pos.config.provider_id[0],
                            'template': self.pos.config.template_id[0],
                            'image': ticketImage,
                            'phone': client.mobile,
                            'id': client.id,
                            'receipt_name': orderName,
                        }).then(function (data) {
                            if (data['error']) {
                                return this.env.services.popup.add(ErrorPopup, {
                                    title: self.env._t(data['error']),
                                });
                            }
                        });
                    }
                } else {
                    $(self.el).find('.send_by_whatsapp').hide()
                }
            });
        });

    },

    async sendByWhatsapp() {
        var def = new $.Deferred();
        var self = this;
        const order = this.currentOrder;
        const client = order.get_partner();
        //
        if (this.currentOrder.get_partner() == null) {
            return this.env.services.popup.add(ErrorPopup, {
                title: _t('Please Select Customer'),
            });
        }
        const phone = client.mobile
        if (phone) {
            $('#phone').val(phone);
        }
        else {
            this.env.services.popup.add(ErrorPopup, {
                title: _t('Mobile Number Required'),
            });
            return false;
        }
        return await this.env.services.popup.add(WaComposerPopup, {
            keepBehind: true,
            ReceiptScreen: this,
            transaction: def,
        });
    }
});

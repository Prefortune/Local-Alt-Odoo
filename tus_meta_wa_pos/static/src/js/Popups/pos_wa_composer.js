/** @odoo-module */

/* global html2canvas */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { registry } from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";
import { BasePrinter } from "@point_of_sale/app/printer/base_printer";
import { _t } from "@web/core/l10n/translation";
import { useRef, onMounted, useState } from "@odoo/owl";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { Input } from "@point_of_sale/app/generic_components/inputs/input/input";
import { useService } from "@web/core/utils/hooks";

export class WaComposerPopup extends AbstractAwaitablePopup {
    static template = "tus_meta_wa_pos.WaComposerPopup";
    static defaultProps = {
        confirmKey: "Enter",
        cancelKey: "Escape",
        ReceiptScreen: false,
        transaction: false
    };

    setup() {
        super.setup();
        this.renderer = useService("renderer");
        this.state = owl.useState({
            templates: this.env.services.pos.templates.filter(t => this.env.services.pos.config.allowed_provider_ids && this.env.services.pos.config.allowed_provider_ids[0] == t.provider_id[0] && t.model == 'pos.order'),
            providers: this.env.services.pos.providers.filter(p => this.env.services.pos.config.allowed_provider_ids.includes(p.id)),
            mobile: this.env.services.pos.selectedOrder.partner.name + ' ( ' +this.env.services.pos.selectedOrder.partner.mobile+' )',
        })
    }

    constructor() {
        super(...arguments);
    }

    onChangeProvider(event) {
        var def = new $.Deferred();
        var self = this;
        const order = self.props.ReceiptScreen.currentOrder;
        const orderName = order.get_name();
        const client = order.get_partner();

        if (client == null) {
            return this.env.services.popup.add(ErrorPopup, {
                title: _('Please Select Customer'),
            });
        }
        this.state.templates = this.props.ReceiptScreen.pos.templates.filter(t => parseInt(event.target.value) == t.provider_id[0] && t.model == 'pos.order');
    }

    async onChangeTemplate(event) {
        var def = new $.Deferred();
        var self = this;
        const order = self.props.ReceiptScreen.currentOrder;
        const orderName = order.get_name();
        const client = order.get_partner();
        const template_id = event.target.value;

        if (client == null) {
            return this.env.services.popup.add(ErrorPopup, {
                title: _('Please Select Customer'),
            });
        }
        await this.env.services.rpc("/get/template/content", {
            'template_id': template_id,
            'order_name': orderName,
        }).then(function (data) {
            if (data) {
                $('#message').val(data)
            }
            else {
                $('#message').val('')
            }
        });
    }

    async onClick() {
        if ($(".wa_template option:selected").val() != '' && $('#message').val() != '' && $(".provider option:selected").val() != '') {
            var self = this;
            const printer = new BasePrinter(null, self.env.services.pos);
            const receiptString = $('.pos-receipt-container').length && $('.pos-receipt-container')[0].innerHTML;
            const ticketImage1 = await html2canvas($('.pos-receipt-container')[0], { addClass: "pos-receipt-print" });
            const ticketImage = ticketImage1.toDataURL("image/png");
            const order = self.props.ReceiptScreen.currentOrder;
            const orderName = order.get_name();
            const client = order.get_partner();
            const phone = client.mobile;
            if (phone) {
                await this.env.services.rpc("/send/receipt", {
                    'message': $('#message').val(),
                    'template': $(".wa_template option:selected").val(),
                    'provider': $(".provider option:selected").val(),
                    'image': ticketImage,
                    'phone': $('#phone').val(),
                    'id': client.id,
                    'receipt_name': orderName,
                }).then(function (data) {
                    if (data['error']) {
                        return self.env.services.popup.add(ErrorPopup, {
                            title: _t(data['error']),
                        });
                    }
                    $('.wa_cancel').click();
                });
            }
            else {
                this.env.services.popup.add(ErrorPopup, {
                    title: this.env._t('Mobile Number Required'),
                });
                return false;
            }
        }
        else {
            this.env.services.popup.add(ErrorPopup, {
                title: this.env._t('Provider, Message and Template are Required!'),
            });
        }
    }
}

registry.add("wa_composer_popup", WaComposerPopup);
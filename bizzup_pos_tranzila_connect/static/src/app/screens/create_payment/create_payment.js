/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class CreatePaymentPopupWidget extends Component {
    static template = "bizzup_pos_tranzila_connect.CreatePaymentPopupWidget";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        amount: { type: Number, optional: true },
        confirmLabel: { type: String, optional: true },
        close: Function,
        paymentlimit: '',
        order_ref: '',
        partner: '',
        getPayload: Function,
    };
    static defaultProps = {
        title: _t("Customer Details"),
        confirmLabel: _t("Confirm"),
        cancelLabel: _t("Discard"),
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({ inputValue: this.props.startingValue });
        this.pos = usePos();
        this.dialog = useService("dialog");
    }

    async confirm() {
        if (this.props.selectedTerminal != null) {
                const selectedLimit = this.props.selectedLimit !== undefined ? this.props.selectedLimit : 0;
                // call get_pos_data to create transaction for pos order
                const result = await this.orm.call("pos.payment", "get_pos_data", [], {
                    selected_limit: selectedLimit,
                    selected_terminal: this.props.selectedTerminal,
                    amount: this.props.amount,
                    selected_partner: this.props.partner,
                    session: this.pos.get_order().session_id.id,
                    name: this.pos.get_order().name,
                });

                if (result) {
                    if (result.transaction_result && result.transaction_result.statusCode !== undefined) {
                        if (result.transaction_result.statusCode !== 0) {
                            this.dialog.add(ConfirmationDialog, {
                                title: _t('Payment Error'),
                                body: _t(result.transaction_result.statusMessage),
                            });
                            return;
                        }
                    } else {
                        this.dialog.add(ConfirmationDialog, {
                            title: _t('Payment Error'),
                            body: _t(result.error || "Unknown error occurred"),
                        });
                        return;
                    }

                    this.pos.get_order().selected_limit = selectedLimit;
                    this.pos.get_order().selected_terminal = this.props.selectedTerminal;

                    this.props.getPayload(this.state);
                    this.props.close();
                }
                this.pos.get_order().selected_limit = selectedLimit;
                this.pos.get_order().selected_terminal = this.props.selectedTerminal;

                this.props.getPayload(this.state);
                this.props.close();
        } else {
            this.dialog.add(ConfirmationDialog, {
                title: _t('Machine ID Warning'),
                body: _t('Please select the POS Machine to proceed.'),
            });
        }
    }

    close() {
        this.props.close();
    }
}

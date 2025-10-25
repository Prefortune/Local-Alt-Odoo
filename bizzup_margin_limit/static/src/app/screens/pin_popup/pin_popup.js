/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";
import { unaccent } from "@web/core/utils/strings";
import { Input } from "@point_of_sale/app/generic_components/inputs/input/input";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class ManagerPINPopup extends Component {
    static template = "bizzup_margin_limit.ManagerPINPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        margin: { type: Number, optional: true },
        confirmLabel: { type: String, optional: true },
        close: Function,
        getPayload: Function,
    };
    static defaultProps = {
        title: _t("Block"),
        confirmLabel: _t("Confirm"),
        cancelLabel: _t("Discard"),
    };
    setup() {
        super.setup();
        this.state = useState({ inputValue: this.props.pin });
        this.orm = useService("orm");
        this.pos = usePos();
        this.dialog = useService("dialog");
    }
    async confirm() {
        const price = 10;
        if (this.props.pin == undefined ) {
            this.dialog.add(ConfirmationDialog, {
                title: _t('קוד מנהל קופה נדרש'),
                body: _t('בבקשה הכנס קוד מנהל .'),
            });
        } else {
            const pin = await this.orm.call('res.users', 'get_manager_pin', [price], {
                cashier: this.pos.get_cashier().id,
            });
            if (pin != false) {
                if (pin != this.props.pin) {
                    this.dialog.add(ConfirmationDialog, {
                        title: _t('קוד שגוי'),
                        body: _t('אנא הכנס את הקוד הנכון של המנהל.'),
                    });
                } else {
                    this.props.getPayload(this.state);
                    this.props.close();

                }
            } else {
                this.dialog.add(ConfirmationDialog, {
                    title: _t('קוד לא נמצא'),
                    body: _t('אנא בקש מהמנהל שלך את הקוד.'),
                });
            }
        }

    }
    close() {
        this.props.close();
    }
}

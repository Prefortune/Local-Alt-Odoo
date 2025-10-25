/** @odoo-module **/
import { Dialog } from "@web/core/dialog/dialog";
import { Component } from "@odoo/owl";

export class BackorderExtDialog extends Component {
    static components = { Dialog };
    static props = {
        displayUoM: Boolean,
        uncompletedLines: Array,
        onApply: Function,
        close: Function,
    };
    static template = "cr_blind_receipt.BackorderDialog";

    async _onApply() {
        await this.props.onApply();
        this.props.close();
    }
}
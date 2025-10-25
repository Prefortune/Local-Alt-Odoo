/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";
import { user } from "@web/core/user";
import { BankRecKanbanUploadController } from "@account_bank_statement_import/bank_reconciliation/kanban";


patch(BankRecKanbanUploadController.prototype, {
    async openCustomReconciliationWizard() {
        this.action.doAction("custom_bank_reconcilation.action_custom_bank_reconcilation_wizard", { additionalContext: this.props.context });
    }
});

/** @odoo-module **/

import { FormController } from '@web/views/form/form_controller';
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
    setup() {
        super.setup();
        this.env.config.resId = this.props.resId;
    }
});

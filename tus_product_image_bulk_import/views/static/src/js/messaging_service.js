/** @odoo-module **/

import { Messaging } from "@mail/core/common/messaging_service";
import { patch } from "@web/core/utils/patch";

patch(Messaging.prototype, {
    async initialize() {
        if(this.env.services.user.context.uid){
            super.initialize(...arguments);
        }
    }
})
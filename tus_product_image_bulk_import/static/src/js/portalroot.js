/** @odoo-module **/

import { Component, xml, useSubEnv } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { PortalchatButton } from "./portal_chat_button";

export class PortalchatRoot extends Component {
    static template = xml`
        <PortalchatButton/>
    `;
    static components = { PortalchatButton };

    setup() {
        useSubEnv({ inShadow: true });
    }
}

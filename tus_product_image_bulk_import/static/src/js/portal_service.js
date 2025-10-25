/* @odoo-module */

import { url } from "@web/core/utils/urls";
import { PortalchatButton } from "./portal_chat_button";
import { _t } from "@web/core/l10n/translation";
import { App } from "@odoo/owl";

import { templates } from "@web/core/assets";
import { registry } from "@web/core/registry";

//registry.category("main_components").remove("mail.ChatWindowContainer");
export const PortalchatService = {
    dependencies: ["mail.messaging"],

    start(env) {
        const app = new App(PortalchatButton, {
            env,
            templates,
            translatableAttributes: ["data-tooltip"],
            translateFn: _t,
            dev: env.debug,
        })
        app.mount(document.getElementById('o_main_nav'));
    },
};
registry.category("services").add("website_portal_chat.portal_chat", PortalchatService);

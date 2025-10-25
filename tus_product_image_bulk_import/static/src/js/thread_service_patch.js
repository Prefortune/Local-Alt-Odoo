/* @odoo-module */

import { ThreadService, threadService } from "@mail/core/common/thread_service";

import { patch } from "@web/core/utils/patch";
import { url } from "@web/core/utils/urls";
import { makeEnv, startServices } from "@web/env";
/** @type {import("@mail/core/common/store_service").Store} */
import Store from "@mail/core/common/store_service"
import { App, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(ThreadService.prototype, {
    openChatwithThread(thread){
        if (!thread) {
            return;
        }
        const chatWindow = this.store.ChatWindow.insert({
            thread,
            folded: thread.state === "folded",
        });
        chatWindow.autofocus++;
        this.setDiscussThread(thread)
    },
});

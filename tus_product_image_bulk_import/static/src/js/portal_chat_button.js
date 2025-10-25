/* @odoo-module */

import { Component, useExternalListener, useState } from "@odoo/owl";

import { useService } from "@web/core/utils/hooks";
import { debounce } from "@web/core/utils/timing";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { ImStatus } from "@mail/core/common/im_status";

import { NotificationItem } from "@mail/core/web/notification_item";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { _t } from "@web/core/l10n/translation";
import { ChannelSelector } from "@mail/discuss/core/web/channel_selector";

export class PortalchatButton extends Component {
    static template = "website_portal_chat.PortalchatButton";
    static DEBOUNCE_DELAY = 500;

    setup() {
        this.store = useState(useService("mail.store"));
        this.chatWindowService = useState(useService("mail.chat_window"));
        /** @type {import('@mail/core/common/thread_service').ThreadService} */
        this.threadService = useService("mail.thread");
       }

    onClickThread(isMarkAsRead, thread){
        this.threadService.openChatwithThread(thread);
        this.threadService.markAsRead(thread);
    }
    get threads() {
        return this.getThreads();
    }
    getThreads() {
        return this.store.menuThreads;
    }
    get counter() {
        let value =
            this.store.discuss.inbox.counter +
            Object.values(this.store.Thread.records).filter(
                (thread) => thread.is_pinned && thread.message_unread_counter > 0
            ).length +
            this.store.failures.reduce((acc, f) => acc + parseInt(f.notifications.length), 0);
        return value;
    }
}
PortalchatButton.components = { DropdownItem,Dropdown,NotificationItem,ImStatus,ChannelSelector }

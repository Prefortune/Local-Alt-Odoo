/* @odoo-module */

import { Component, useRef, useState } from "@odoo/owl";
import { useEmojiPicker } from "@web/core/emoji_picker/emoji_picker";
import { useService } from "@web/core/utils/hooks";

/**
 * @typedef {Object} Props
 * @property {import("models").Message} message
 * @extends {Component<Props, Env>}
 */
export class PfCreateTicketButton extends Component {
    static template = "pf_alt_website_custom.PfCreateTicket";
    static props = ["ticket"];

    setup() {
        this.messageService = useState(useService("mail.message"));
        this.store = useState(useService("mail.store"));
    
    }
}

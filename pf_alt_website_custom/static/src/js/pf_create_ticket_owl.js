/** @odoo-module **/
import {
    patch
} from "@web/core/utils/patch";
import {
    useService
} from "@web/core/utils/hooks";
import {
    Message
} from "@mail/core/common/message";
patch(Message, {
    components: {
        ...Message.components
    },
});
import { _t } from "@web/core/l10n/translation";
import { messageActionsRegistry } from "@mail/core/common/message_actions";

function stripHtmlTags(html) {
    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = html;
    return tempDiv.textContent || tempDiv.innerText || ""; // Extract plain text
}


patch(Message.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
    },
    async createTicket() {
        var self = this
        var plainMessage = stripHtmlTags(this.message.body);
        var customerId = await this.getCustomerIdFromMessage(this.message.id);
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "sh.helpdesk.ticket",
            target: "new",
            views: [[false, "form"]],
            context: {
                default_description: this.message.body, // Prefill the 'review' field with the message content
                default_partner_id: customerId,
                default_email_subject: 'Message ticket....'
            },
        });

    },
    async getCustomerIdFromMessage(messageId) {
       // try {
            // Query the mail.message to get related partner information
            const partnerId = await this.orm.call(
                "mail.message", // Model name
                "search_read", // RPC method to fetch data
                [[["id", "=", messageId]]], // Search domain to find the message by ID
                { fields: ["author_id"], limit: 1 } // Get partner_id of the message
            );
            if (partnerId && partnerId.length > 0) {
                return partnerId[0].author_id[0]; // Return the partner ID (res_id) from the result
            } else {
                console.log("No related partner found for message ID:", messageId);
                return null;
            }
        // } catch (error) {
        //     console.error("Error fetching customer ID for message ID:", error);
        //     return null;
        // }
    }
})



messageActionsRegistry.add("pf_create_ticket", {
	condition: (component) => component.canReplyTo,
	icon: "fa-ticket",
	title: () => _t("Create ticket"),
	onClick: (component) => component.createTicket(),
	sequence: 0,
})
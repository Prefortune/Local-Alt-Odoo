/* @odoo-module */

import { ChannelSelector } from "@mail/discuss/core/web/channel_selector";

import { cleanTerm } from "@mail/utils/common/format";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";


//Search Whatsapp Channel For Name and Mobile No
patch(ChannelSelector.prototype, {
    async fetchSuggestions() {
        super.fetchSuggestions(...arguments)
        const cleanedTerm = cleanTerm(this.state.value);
           if (this.props.category.id === "WpChannels" && this.state.value) {
            const results = await this.sequential(async () => {
                this.state.navigableListProps.isLoading = true;
                const res = await this.orm.call("discuss.channel", "whatsapp_channel_search", [
                    cleanedTerm,
                    cleanedTerm,
                ]);
                this.state.navigableListProps.isLoading = false;
                return res;
            });
            if (!results) {
                this.state.navigableListProps.options = [];
                return;
            }
            const suggestions = this.suggestionService
                .sortPartnerSuggestions(results, cleanedTerm)
                .map((data) => {
                    this.store.Persona.insert({ ...data, type: "partner" });
                    return {
                        classList: "o-discuss-ChannelSelector-suggestion",
                        label: data.name,
                        partner: data,
                    };
                });
            if (this.store.self.name.includes(cleanedTerm)) {
                suggestions.push({
                    classList: "o-discuss-ChannelSelector-suggestion",
                    label: this.store.self.name,
                    partner: this.store.self,
                });
            }
            if (suggestions.length === 0) {
                suggestions.push({
                    classList: "o-discuss-ChannelSelector-suggestion",
                    label: _t("No results found"),
                    unselectable: true,
                });
            }
            this.state.navigableListProps.options = suggestions;
            return;
        }
    },
    onSelect(option) {
    super.onSelect(...arguments)
        if (this.props.category.id === "WpChannels") {
             if (!this.state.selectedPartners.includes(option.partner.id)) {
                this.state.selectedPartners.push(option.partner.id);
            }
            this.state.value = "";
            this.onValidate();
        }
    },
    async onValidate() {
    super.onValidate(...arguments)
        if (this.props.category.id === "WpChannels") {
            const selectedPartnerIds = this.state.selectedPartners;
            if (selectedPartnerIds.length === 0) {
                return;
            }
            await this.discussCoreCommonService.startChat(
                selectedPartnerIds,
                this.env.inChatWindow
            );
        }
    },
});
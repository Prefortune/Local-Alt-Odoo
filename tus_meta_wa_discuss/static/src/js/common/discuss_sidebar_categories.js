/* @odoo-module */

import { discussSidebarCategoriesRegistry } from "@mail/discuss/core/web/discuss_sidebar_categories";
import { patch } from "@web/core/utils/patch";
import { DiscussAppCategory } from "@mail/core/common/discuss_app_category_model";
import { compareDatetime } from "@mail/utils/common/misc";
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { DiscussSidebarCategories } from '@mail/discuss/core/web/discuss_sidebar_categories';


discussSidebarCategoriesRegistry.add(
    "WpChannels",
    {
//        predicate: (store) => store.discuss.WpChannels.threads.some((thread) => thread?.is_pinned),
        value: (store) => store.discuss.WpChannels,
     },
    { sequence: 30 }
);


// CHANGES FOR SORTING
patch(DiscussAppCategory.prototype, {

    /**
     * @param {import("models").Thread} t1
     * @param {import("models").Thread} t2
     */

    sortThreads(t1, t2) {
        if (this.id === "WpChannels") {
            return (
                compareDatetime(t2.lastInterestDateTime, t1.lastInterestDateTime) || t2.id - t1.id
            );
        }
        return super.sortThreads(t1, t2);
    },


});


patch(DiscussSidebarCategories.prototype,{
    setup(){
        super.setup()
         this.rpc = useService("rpc");
         this.orm = useService("orm");
         this.wpchannel = this.categories.find((categ) => categ.value(this.store).id == "WpChannels")
    },

    async onClickUpdateMesssageLimit() {
        let default_limit = await this.orm.call('res.users', 'get_limit_show', []);
        let limit = this.env.services.user.context.limit ? this.env.services.user.context.limit + default_limit.show :  default_limit.show + default_limit.default_show
        this.env.services.user.updateContext({'limit': limit})
        var self = this;
    //        var init_messaging_temp = await this.env.services["mail.messaging"].initialize();
        var temp = await this.rpc("/mail/init_messaging",{ context: this.env.services.user.context });
        for (const cust_channel of temp.channels) {
            await self.threadService.fetchChannel(cust_channel.id)
        }
    },
});

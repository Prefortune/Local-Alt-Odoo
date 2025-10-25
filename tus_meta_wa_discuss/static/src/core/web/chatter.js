/** @odoo-module */

import { ThreadService } from "@mail/core/common/thread_service";
import { parseEmail } from "@mail/js/utils";

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(ThreadService.prototype, {
    async fetchData(
        thread,
        requestList = ["activities", "followers", "attachments", "messages", "suggestedRecipients"]
    ){
     const res = await super.fetchData(...arguments);
        var lst =  res['not_send_msgs_btn_in_chatter'].filter((r) => r == thread.model);
        var wpLst = res['not_wa_msgs_btn_in_chatter'].filter((r) => r == thread.model);
        thread['DisableSendMessageBtn'] = lst.length > 0 ? false : true;
        thread['DisableWpSendMessageBtn'] = wpLst.length > 0 ? false : true;
    //    if (lst.length > 0){
    //    }else{
    //        thread['DisableSendMessageBtn'] = true
    //    }
        return res

    }
})

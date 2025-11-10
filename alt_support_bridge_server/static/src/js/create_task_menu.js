import { messageActionsRegistry } from "@mail/core/common/message_actions";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

messageActionsRegistry.add("create-task", {
    condition: (component) =>
        component.store.self.isInternalUser &&
        component.props.thread?.model === "discuss.channel",
        icon: "fa fa-tasks",

    onClick: async (component) => {

        const message = component.props.message; 
        const author = message.author;
        const project_name = component.props.thread.name;
        const res_id = component.props.thread.id;

        console.log("------------> message",message.body);
        

        if(res_id && project_name){
            const result = await rpc('/alt_support_bridge_server/ensure_project', {
                channel_id: res_id,
                channel_name: project_name,
                author_id: author.id,
                message : message.body || "",

            });
            const actionService = component.env.services.action;
            const notification = component.env.services.notification
            if(result.error){
                notification.add(_t(result.error), {
                    type: "danger",
                });
                return
            }
            
            if(result.subscriptions === false){
                notification.add(_t("Please Create SubScription For User No Any Valid Subscription Avalible."), {
                    type: "danger",
                });
                return
            }
            actionService.doAction({
                    name: _t("Create Task"),
                    type: 'ir.actions.act_window',
                    res_model: 'project.task.create.wizard',
                    view_mode: 'list,form',
                    views: [[false, 'form']],
                    target: 'new',
                    context: { default_project_id: result.project_id , 
                               default_user_id :  result.user_id, 
                               default_alt_subscription_id : result.subscriptions,
                               default_description : result.message 
                    },
                });
        }
    },
    title: () => _t("Create Task"),
    sequence: 80,
});

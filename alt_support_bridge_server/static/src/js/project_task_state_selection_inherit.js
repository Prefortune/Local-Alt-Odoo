/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ProjectTaskStateSelection } from "@project/components/project_task_state_selection/project_task_state_selection";

export const projectTaskStateSelection_Alt = {
    setup() {
        super.setup(...arguments);
        console.log("--- patched ProjectTaskStateSelection ---");
        this.icons = {
            "00_new_state" : "fa fa-lg fa-star-o",
            "01_in_progress": "o_status",
            "03_approved": "o_status o_status_green",
            "02_changes_requested": "fa fa-lg fa-exclamation-circle",
            "1_done": "fa fa-lg fa-check-circle",
            "1_canceled": "fa fa-lg fa-times-circle",
            "04_waiting_normal": "fa fa-lg fa-hourglass-o",
            "05_finished" : "fa fa-lg fa-flag-checkered",
        };
        this.colorIcons = {
            "00_new_state": "text-info",
            "01_in_progress": "",
            "03_approved": "text-success",
            "02_changes_requested": "o_status_changes_requested",
            "1_done": "text-success",
            "1_canceled": "text-danger",
            "04_waiting_normal": "btn-outline-info",
            "05_finished" : "text-success",
        };
        this.colorButton = {
            "00_new_state": "btn-outline-info",
            "01_in_progress": "btn-outline-secondary",
            "03_approved": "btn-outline-success",
            "02_changes_requested": "btn-outline-warning",
            "1_done": "btn-outline-success",
            "1_canceled": "btn-outline-danger",
            "04_waiting_normal": "btn-outline-info",
            "05_finished" : "btn-outline-success",

        };
    },
    get options() {
        const superOptions = super.options || [];
        const labels = new Map(superOptions);
        labels.set("00_new_state", "New");
        labels.set("05_finished", "Finished");
        const states = ["1_canceled", "1_done", "05_finished"];
        const currentState = this.props.record.data[this.props.name];
        if (currentState != "04_waiting_normal") {
            states.unshift("00_new_state", "01_in_progress", "02_changes_requested", "03_approved",);
        }
        return states.map((state) => [state, labels.get(state)]);
    }

};

patch(ProjectTaskStateSelection.prototype, projectTaskStateSelection_Alt);

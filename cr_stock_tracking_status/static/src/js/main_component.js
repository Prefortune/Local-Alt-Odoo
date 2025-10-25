import MainComponent from "@stock_barcode/components/main";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

patch(MainComponent.prototype, {
    setup() {
        super.setup();
        this.state.tracking_status = false;
        this.get_status();
    },

    async get_status() {
        const data = await rpc("/web/dataset/call_kw", {
            model: this.resModel,
            method: "read",
            args: [[this.resId], ["tracking_status"]],
            kwargs: {},
        });
        console.log(data);
        if (data?.[0]?.tracking_status) {
            const currentStatus = data[0].tracking_status;
            this.state.tracking_status = this.getStatusDisplay(currentStatus);
            this.state.next_tracking_status = this.getNextStatusDisplay(currentStatus);
        }
    },

    getStatusDisplay(currentStatus) {
        const statusMap = {
            'none': 'None',
            'uploaded': 'העמס',
            'drive': 'התחל נהיגה',
            'downloaded': 'פרוק סחורה',
            'done': 'סיים וחתום',
        };
        return statusMap[currentStatus] || currentStatus; // Return display label or current status if invalid
    },

    getNextStatusDisplay(currentStatus) {
        const statusMap = {
            'none': 'None',
            'uploaded': 'העמס',
            'drive': 'התחל נהיגה',
            'downloaded': 'פרוק סחורה',
            'done': 'סיים וחתום',
        };
        const statusSequence = ['none', 'uploaded', 'drive', 'downloaded', 'done'];

        if (currentStatus === 'done') {
            return statusMap['done']; // If status is 'done', return 'Done'
        }

        const currentIndex = statusSequence.indexOf(currentStatus);
        if (currentIndex === -1 || currentIndex === statusSequence.length - 1) {
            return statusMap[currentStatus] || currentStatus; // Return current display label or status if invalid
        }

        const nextStatus = statusSequence[currentIndex + 1];
        return statusMap[nextStatus];
    },

    async callServerAction() {
        const result = await rpc("/web/dataset/call_kw", {
            model: this.resModel,
            method: "change_tracking_status",
            args: [[this.resId]],
            kwargs: {},
        });

        const { model } = this.env;
        let display = model.displaySignatureButton;
        let canOpen = false;

        try {
            const canOpenResult = await rpc("/web/dataset/call_kw", {
                model: this.resModel,
                method: "can_show_signature_modal",
                args: [[this.resId]],
                kwargs: {},
            });
            canOpen = canOpenResult === true;
        } catch (error) {
            console.warn("Failed to fetch backend condition:", error);
        }

        if (display && canOpen) {
            this.env.model.openSignatureDialog();
        }

        // Fetch the updated status after the server action
        const data = await rpc("/web/dataset/call_kw", {
            model: this.resModel,
            method: "read",
            args: [[this.resId], ["tracking_status"]],
            kwargs: {},
        });

        if (result && data?.[0]?.tracking_status) {
            const newStatus = data[0].tracking_status;
            const displayStatus = this.getStatusDisplay(newStatus);
            const nextStatusDisplay = this.getNextStatusDisplay(newStatus);
            this.state.tracking_status = displayStatus;
            this.state.next_tracking_status = nextStatusDisplay;
            this.env.services.notification.add(`סטטוס העמסה עודכן ל-${displayStatus}!!`, { type: "success" });
        } else {
            this.env.services.notification.add("Tracking Status is already at final stage or failed to update.", { type: "warning" });
        }
    },

    onClickChangeStatus() {
        this.callServerAction();
    },
});
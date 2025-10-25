/** @odoo-module **/

import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

patch(ControlPanel.prototype, {

    setup() {
    super.setup();

     this.modelName = this.env.config && this.env.config.actionName ? this.env.config.actionName : "";
    this.viewType = this.env.config && this.env.config.viewType ? this.env.config.viewType : "";

     const rawArch = this.env.config && this.env.config.rawArch ? this.env.config.rawArch : "";

    const isPackageForm = rawArch.includes('<form string="Package">') || rawArch.includes('<form string="חבילה">');

     this.isProductKanban = (this.modelName === "Packages" && this.viewType === "form") || isPackageForm;

     this.onClickChangeStatus = this.onClickChangeStatus.bind(this);
},
    async onClickChangeStatus() {
        const resId = this.env.config?.resId;
        const res = await rpc("/web/dataset/call_kw", {
            model: "stock.quant.package",
            method: "read",
            args: [resId, ["load_status"]],
            kwargs: {},
        });

        const updates = res.map((rec) => {
            let new_status = "none";
            if (rec.load_status === "none") new_status = "loaded";
            else if (rec.load_status === "loaded") new_status = "downloaded";
            else if (rec.load_status === "downloaded") new_status = "none";
            return { id: rec.id, new_status };
        });

        for (const u of updates) {
            await rpc("/web/dataset/call_kw", {
                model: "stock.quant.package",
                method: "write",
                args: [[u.id], { load_status: u.new_status }],
                kwargs: {},
            });
        }

        window.location.reload();
    },

});
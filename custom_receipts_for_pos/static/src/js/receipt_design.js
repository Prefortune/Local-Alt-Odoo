/** @odoo-module */
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";
import { useState, Component, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(OrderReceipt.prototype, {
    setup(){
        super.setup();
        console.log("Custom Receipt Design Loaded");
        this.state = useState({
            template: true,
        })
        this.pos = useState(useService("pos"));
        // console.log("this is pos", this.pos);
        // console.log("this is pos", this.pos.company.id);

        this.loadCompanyLogo(); // ✅ call the loader

        // console.log("Company Logo:", this.company.logo);
        console.log("this is props", this.props);
        console.log("this is props data", this.props.data);
        console.log("this is props data orderlines", this.props.data.paymentlines);
        console.log("this is props data orderlines", this.props.data.paymentlines.name);
        console.log("this is props data orderlines", this.props.data.paymentlines.amount);

    },
    async loadCompanyLogo() {
    const [company] = await this.env.services.orm.searchRead(
        "res.company",
        [["id", "=", this.pos.company.id]],
        ["logo"]
    );
    if (company && company.logo) {
        this.pos.company.logo = company.logo; // ✅ assign correctly
        // console.log("✅ Loaded company logo (base64):", company.logo);
    } else {
        console.warn("⚠️ Company logo not found or empty in DB.");
    }
},
    get templateProps() {
        // console.log("Custom Receipt Design Props Loaded");
        const order = this.pos.get_order();
        const partner = order ? order.get_partner() : null;

        return {
            pos:this.pos,
            data: this.props.data,
            order: order,
            receipt:this.props.data,
            orderlines:this.props.data.orderlines,
            paymentlines:this.props.data.paymentlines,
            partner: partner,
        };
    },
    get templateComponent() {
        // console.log("Custom Receipt Design Component Loaded");
        var mainRef = this;
        return class extends Component {
            setup() {}
            static template = xml`${mainRef.pos.config.design_receipt}`
        };
    },
    get isTrue() {
        if (this.env.services.pos.config.is_custom_receipt == false) {
            return true;
        }
        return false;
    }
});

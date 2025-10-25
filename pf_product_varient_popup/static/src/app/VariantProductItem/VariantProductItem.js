/** @odoo-module */

import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class VariantProductItem extends Component {
    static template = "pf_product_varient_popup.VariantProductItem";

    setup() {
        this.pos = usePos();
    }
}

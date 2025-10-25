/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { VariantProductItem } from "@pf_product_varient_popup/app/VariantProductItem/VariantProductItem";
import { usePos } from "@point_of_sale/app/store/pos_hook";


export class VariantPopup extends AbstractAwaitablePopup {
    static components = { VariantProductItem };
    static template = "pf_product_varient_popup.VariantPopup";
    setup() {
        super.setup();
        this.product_varaints = []
        this.pos = usePos()
    }   
    clickProduct(product) {
        if(product){
            this.pos.addProductToCurrentOrder(product)
            if (this.pos.config.pf_close_popup_after_single_selection) {
                this.confirm()
            }
        }
    }
    get VariantProductToDisplay() {
        if (this.productFilter && this.productFilter.length > 0) {
            return this.productFilter
        } else {
            return this.props.product_variants;
        }
    }
    updateSearch(event) {
        var val = event.target.value || ""
        var searched_varaints = this.pos.db.search_variants(this.props.product_variants, val);
        if (searched_varaints && searched_varaints.length > 0) {
            this.productFilter = searched_varaints
        } else {
            this.productFilter = []
        }
        this.render()
    }
}
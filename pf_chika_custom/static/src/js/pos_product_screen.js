/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    // Override product display to include category
    getProductDisplayName(product) {
        let displayName = product.display_name;
        if (product.name) {
            displayName += `\n${product.name}`;
        }
        return displayName;
    }
});
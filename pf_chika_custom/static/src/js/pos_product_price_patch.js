/** @odoo-module */

import { Product } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";




patch(PosStore.prototype, {
    /**
     * @override
     */
 
    async _processData(loadedData) {      
        await super._processData(...arguments);
        this.product_temp = loadedData['product.product'];
    },  

});

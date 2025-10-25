/** @odoo-module */

import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(PaymentScreen.prototype, {
    async sizechartButton() {
        const order = this.pos.get_order();
        console.log("........................order...............",order,this.pos.backendId);
        if (!order.backendId) {
            this.popup.add(ErrorPopup, {
                title: 'POS Order Not Found',
                body: 'This POS order is not synced to the backend yet.',
            });
            return;
        }
    
        const url = `/web#id=${order.backendId}&model=pos.order&view_type=form`;
        window.open(url, '_blank');
    },
    async validateOrder(isForceValidate) {
        await super.validateOrder(...arguments); 
        console.log("..............................this.currentOrder...",this.currentOrder);
        if (this.currentOrder.server_id){            
            const url = `/web#id=${this.currentOrder.server_id}&cids=1&menu_id=240&action=390&model=pos.order&view_type=form`;
            await window.open(url, '_blank');
        }        
    }                
});
patch(Orderline.prototype,{
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);        
        this.pf_size_chart_id = this.pf_size_chart_id || false; 
        console.log("...................json......",json.pos_order_id);      
    },   
})
export class OrderlinesizechartButton extends Component {
    static template = "pf_chika_size_chart.OrderlinesizechartButton";

    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
        this.orm = useService("orm");
    }
    async onClick() {        
        const order = this.pos.get_order();
        const orderData = order.export_as_JSON();
        console.log("......................orderData....",orderData);
        // const posorder = await this.orm.call("pos.order", "search_read", [], { fields: ["id", "name"] });
        // console.log(".......posorder....",posorder);
        // if (!order.backendId) {
        //     this.popup.add(ErrorPopup, {
        //         title: 'POS Order Not Found',
        //         body: 'This POS order is not synced to the backend yet.',
        //     });
        //     return;
        // }
    
        // const url = `/web#id=${order.backendId}&model=pos.order&view_type=form`;
        // window.open(url, '_blank');
        // this.popup.add(SizeChartPopup, {
        //     title: "Select Size Chart",
        //     onSelect: async (payload) => {
        //         const order = this.pos.get_order();
        //         const orderline = order.get_selected_orderline();
        //         if (orderline) {
        //             orderline.pf_size_chart_id = payload.id;
        //             orderline.trigger("change", orderline);
        //             console.log(`Size chart set: ${payload.name}`);
        //         }
        //     },
        // });
    }
}

ProductScreen.addControlButton({
    component: OrderlinesizechartButton,
});
/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";

export class SizeChartPopup extends Component {    
    static template = "pf_chika_size_chart.SizeChartPopup";
    setup() {
        this.pos = usePos();
        this.orm = useService("orm");
        this.popup = useService("popup");
        this.sizeCharts = [];
        this.state = useState({
            searchQuery: "",
            sizeCharts: [],
            filteredCharts: [],
        });
        this.selectSizeChart = this.selectSizeChart.bind(this);
        this.loadSizeCharts();
    }
    onSearchInput(event) {
        const query = event.target.value.toLowerCase();
        this.state.searchQuery = query;
        this.state.filteredCharts = this.state.sizeCharts.filter(chart =>
            chart.name.toLowerCase().includes(query)
        );
    }
    async loadSizeCharts() {
        try {
            const charts = await this.orm.call("pf.size.chart", "search_read", [], { fields: ["id", "name"] });
            console.log("....................charts....1",charts);
            this.state.sizeCharts = charts;
            this.state.filteredCharts = charts;
        } catch (error) {
            console.error("Failed to load size charts", error);
        }
    }

    selectSizeChart(sizeChart) {
        console.log("........................this....",this);
        const order = this.pos.get_order();
        const orderline = order.get_selected_orderline();
        if (orderline) {
            orderline.pf_size_chart_id = sizeChart.id;
            // orderline.update({ size_chart_id: sizeChart.id });
            console.log(`Size chart set: ${orderline.pf_size_chart_id}`);
        }
        // this.trigger("size-chart-selected", { id: sizeChart.id, name: sizeChart.name });
        this.props.close(); 
    }
    closePopup() {
        console.log("...this....",this);
        this.props.close(); 
    }
}
/** @odoo-module **/

import VariantMixin from '@website_sale/js/sale_variant_mixin';
import "@website_sale/js/website_sale";
//import { qweb as QWeb } from "web.core";

const stockChangeCombination = VariantMixin._onChangeCombinationStock;
/**
 * @override
 */
VariantMixin._onChangeCombinationStock = function (ev, $parent, combination) {
    stockChangeCombination.apply(this, arguments);
    $('div.availability_messages').html("");
};
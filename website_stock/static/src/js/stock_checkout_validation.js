/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

    publicWidget.registry.stockCheckoutValidation = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'click .remove-cart-line': '_onClickRemoveCartLine',
        },

        _onClickRemoveCartLine: function (ev) {
        debugger;
            var $dom = $(ev.currentTarget);
            var line_id = parseInt($dom.data('line-id'), 10);
            var product_id = parseInt($dom.data('product-id'), 10);
            rpc('/shop/cart/update_json',{
                'line_id': line_id,
                'product_id': product_id,
                'set_qty': 0.0,
            }).then(function(data) {
                var $q = $(".my_cart_quantity");
                $q.parent().parent().removeClass("hidden", !data.quantity);
                $q.html(data.cart_quantity).hide().fadeIn(600);
                location.reload();
            });
        },
        _onChangeJsQuantity: function (ev) {
        debugger;
            var $dom = $(ev.currentTarget);
            var line_id = parseInt($dom.data('line-id'), 10);
            var product_id = parseInt($dom.data('product-id'), 10);
            rpc('/shop/cart/update_json',{
                'line_id': line_id,
                'product_id': product_id,
                'set_qty': 0.0,
            }).then(function(data) {
                var $q = $(".my_cart_quantity");
                $q.parent().parent().removeClass("hidden", !data.quantity);
                $q.html(data.cart_quantity).hide().fadeIn(600);
                location.reload();
            });
        },
    });


/* Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */

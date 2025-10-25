/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";
import WebsiteSale from '@website_sale/js/website_sale';
import { rpc } from "@web/core/network/rpc";

//import { rpc } from "@web/core/network/rpc";

//    var publicWidget = require('web.public.widget');
//    require('website_sale.website_sale');

//    var _t = core._t;
    var temp = '1';

    publicWidget.registry.StockQuntityVaildation = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'change .oe_cart input.js_quantity': '_onChangeJsQuantity',
            'change input[type="text"][name="add_qty"]': '_onChangeAddQty',
            'click a.btn.btn-default.btn-xs': '_onclickDefaultBtn',
        },

        _onChangeJsQuantity: function (ev) {
        debugger;
            var $input = $(ev.currentTarget);
            var value = parseInt($input.val(), 10);
            var $dom = $(ev.currentTarget).closest('tr');
            var line_id = parseInt($input.data('line-id'), 10);
            var product_id = parseInt($input.data('product-id'), 10);
            rpc('/shop/cart/update_json/msg',{
                 'line_id': line_id,
                 'product_id': parseInt($input.data('product-id'), 10,),
                 'set_qty': value,
            }).then(function(msg) {
                console.log(msg);
                if (msg) {
                    console.log("test1"+msg);
                    $dom.popover({
                        content: _t("You are Trying to Add More Than Available Quantity of Product."),
                        title: _t("WARNING"),
                        placement: "top",
                        trigger: 'focus',
                    });
                    $dom.popover('show');
                    setTimeout(function() {
                        $dom.popover('dispose')
                    }, 1000);
                } else {
                    $dom.popover('dispose');
                }
            });
        },

        _onChangeAddQty: function (ev) {
        debugger;
            var $form = $('input.form-control.quantity').closest('form');
            if ($("input[name='product_id']").is(':radio'))
                var product_id = $("input[name='product_id']:checked").attr('value');
            else
                var product_id = $("input[name='product_id']").attr('value');
            var add_qty = parseFloat($form.find('input[type="text"][name="add_qty"]').first().val(), 10);
            rpc('/shop/cart/update/msg',{
                 'product_id': product_id,
                 'add_qty': add_qty,
            }).then(function(result) {
                if (result.status == 'deny') {
                    if (add_qty > result.remain_qty && result.remain_qty > 0) {
                        temp = result.remain_qty.toString();
                    } else {
                        temp = "1";
                    }
                    $form.find('input[type="text"][name="add_qty"]').first().val(temp);
                    $('.css_quantity').popover({
                        content: _t("You Can Not Add More Quantity."),
                        title: _t("WARNING"),
                        placement: "top",
                        trigger: 'focus',
                    });
                    $('.css_quantity').popover('show');
                    setTimeout(function() {
                        $('.css_quantity').popover('dispose')
                    }, 1000);
                } else {
                    $('.css_quantity').popover('dispose');
                    temp = add_qty.toString();
                }
            });
        },

        _onclickDefaultBtn: function (ev) {
        debugger;
            var $form = $(ev.currentTarget).closest('form');
            var $msg = $form.find('.fa-shopping-cart');
            var product_id = parseInt($form.find('input[type="hidden"][name="product_id"]').first().val(), 10);
            rpc('/shop/cart/update/msg',{
                'product_id': product_id, 'add_qty': add_qty,
               }).then(function(result) {
                if (result.status == 'deny') {
                    $(ev.currentTarget).addClass('disabled');
                    alert(_t("You Can Not Add This Product in Your Cart."))
                }

            });
        },
    });

    publicWidget.registry.WebsiteSale.include({
        _onClickAdd: function (ev) {
        debugger;
            var self = this;
            var p_super = this._super;
            var args = ev;

            ev.preventDefault();

            var $form = $(ev.currentTarget).closest('form');
            if ($("input[name='product_id']").is(':radio'))
                var product_id = $("input[name='product_id']:checked").attr('value');
            else
                var product_id = $("input[name='product_id']").attr('value');
            var add_qty = parseFloat($form.find('input[type="text"][name="add_qty"]').first().val(), 10);
            rpc('/shop/cart/update/msg',{
            'product_id': product_id, 'add_qty': add_qty,
            }).then(function(result) {
                if (result.status == 'deny') {
                    $form.find('input[type="text"][name="add_qty"]').first().val(temp);
                    $('#add_to_cart').popover({
                        content: _t("You Already Added All Available Quantity of Product in Your Cart, You Can not Add More Quantity."),
                        title: _t("WARNING"),
                        placement: "left",
                        trigger: 'focus',
                    });
                    $('#add_to_cart').popover('show');
                    setTimeout(function() {
                        $('#add_to_cart').popover('dispose')
                    }, 1000);

                } else {
                    $('#add_to_cart').popover('dispose');
                    return p_super.apply(self, [args]);
                }
            });

        },
    });




/* Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */

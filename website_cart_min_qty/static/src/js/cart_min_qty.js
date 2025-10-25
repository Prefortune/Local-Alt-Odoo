/* global odoo */
odoo.define('website_cart_min_qty.cart_min_qty', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.CartMinQty = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'click .js_add_cart_json': '_onAddToCart',
            'change .js_quantity': '_onQuantityChange',
        },

        start: function () {
            this._super.apply(this, arguments);
            this._bindEvents();
        },

        _bindEvents: function () {
            var self = this;
            // Bind to add to cart buttons
            this.$('.js_add_cart_json').on('click', function (e) {
                self._onAddToCart(e);
            });
        },

        _onAddToCart: function (ev) {
            var $button = $(ev.currentTarget);
            var productId = $button.data('product-id');
            var $quantity = $button.closest('form').find('.js_quantity');
            var quantity = parseInt($quantity.val()) || 1;

            if (productId) {
                this._validateMinQuantity(productId, quantity, $button);
            }
        },

        _onQuantityChange: function (ev) {
            var $input = $(ev.currentTarget);
            var productId = $input.data('product-id');
            var quantity = parseInt($input.val()) || 1;

            if (productId) {
                this._validateMinQuantity(productId, quantity, $input);
            }
        },

        _validateMinQuantity: function (productId, quantity, $element) {
            var self = this;
            
            ajax.jsonRpc('/shop/min_qty_info', 'call', {
                product_id: productId
            }).then(function (result) {
                if (result.enabled && quantity < result.min_qty) {
                    self._showMinQtyError(result, quantity, $element);
                    return false;
                }
                return true;
            });
        },

        _showMinQtyError: function (minQtyInfo, currentQty, $element) {
            var message = 'Minimum quantity for ' + minQtyInfo.product_name + 
                         ' is ' + minQtyInfo.min_qty + '. ' +
                         'You tried to add ' + currentQty + ' items. ' +
                         'Please add at least ' + minQtyInfo.min_qty + ' items.';
            
            // Remove existing error messages
            $('.min-qty-error').remove();
            
            // Create error message element
            var $error = $('<div class="alert alert-warning min-qty-error" role="alert">' +
                          '<strong>Minimum Quantity Required:</strong> ' + message +
                          '</div>');
            
            // Insert error message
            if ($element.closest('.product_detail').length) {
                $element.closest('.product_detail').prepend($error);
            } else {
                $element.closest('form').prepend($error);
            }
            
            // Scroll to error message
            $('html, body').animate({
                scrollTop: $error.offset().top - 100
            }, 500);
            
            // Auto-hide after 5 seconds
            setTimeout(function () {
                $error.fadeOut();
            }, 5000);
        }
    });

    return publicWidget.registry.CartMinQty;
});

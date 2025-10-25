/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProductSalePrice = publicWidget.Widget.extend({
    selector: '#products_grid',

    start() {
        this._super(...arguments);
        this._update_prices();
    },

    _update_prices() {

        
        const forms = document.querySelectorAll('form');
        console.log("res ---------------- ", forms);
        forms.forEach(form => {
            // Check if it's a product form by looking for hidden inputs
            const productIdInput = form.querySelector('input[name="product_id"]');
            const templateIdInput = form.querySelector('input[name="product_template_id"]');

            if (productIdInput && templateIdInput) {
                const productId = productIdInput.value;
                const templateId = templateIdInput.value;

                console.log("productId - templateId:", productId, templateId);

                // Optional: get price
                const priceEl = form.querySelector('.product_price .oe_currency_value');
                console.log("price el ", priceEl)
                const price = priceEl ? parseFloat(priceEl.innerText) : 0;
                // const newPrice = price * 2;
                // priceEl.innerText = newPrice.toFixed(2); // Keep 2 decimals

                // priceEl.innerText(price + price)
                console.log("price:", price);

            }
        });




    },
});

export default publicWidget.registry.ProductSalePrice;
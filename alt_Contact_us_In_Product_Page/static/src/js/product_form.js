import "@website/snippets/s_website_form/000";  // force deps
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.s_website_form.include({

    /**
     * @override
     */
    start: async function () {
        const res = this._super(...arguments);
        this._updateProductName(); // Initial load
        this._bindAttributeChange(); // Bind change event
        return res;
    },

    /**
     * Updates the product name field with selected attributes.
     */
    _updateProductName: function () {
        let inputField = this.$el.find("input[name='Product name']");
        let productName = $("h1[itemprop='name']").text().trim();

        // Find selected attributes within visible .variant_attribute
        let selectedAttributes = [];
        $(".variant_attribute").not(".d-none").each(function () {
            let selectedInput = $(this).find("input:checked");
            if (selectedInput.length) {
                let attributeName = $(this).data("attribute_name");
                let selectedValue = selectedInput.data("value_name");
                selectedAttributes.push(`${attributeName}: ${selectedValue}`);
            }
        });

        // Combine product name with selected attributes
        let finalProductName = productName;
        if (selectedAttributes.length) {
            finalProductName += " (" + selectedAttributes.join(", ") + ")";
        }

        // Set the value in the input field
        inputField.val(finalProductName);
        //inputField.prop("readonly", true);
        inputField.closest('.s_website_form_custom').removeClass('s_website_form_field col-12');
    },

    /**
     * Binds the change event to attribute selection inputs.
     */
    _bindAttributeChange: function () {
        let self = this;
        $(document).on("change", ".variant_attribute input", function () {
            self._updateProductName();
        });
    }
});

publicWidget.registry.ChangePriceDirectionProductPage = publicWidget.Widget.extend({
    selector: '.js_product.js_main_product',

    init() {
        this._super(...arguments);
    },
    start() {
        this.$el.find('.css_editable_mode_hidden').css('direction', 'ltr');

        let priceElement = document.querySelector(".oe_price .oe_currency_value");

        setTimeout(() => {
            if (priceElement) {
                let priceText = priceElement.textContent.trim();
                let updatedPrice = priceText.replace(/(\.00)$/, ""); // Remove .00 if present
                priceElement.textContent = updatedPrice; // Update the element
            }
        }, 500);
        
        return this._super.apply(this, arguments);
    },
});

publicWidget.registry.ChangePriceDirectionShopPage = publicWidget.Widget.extend({
    selector: '.o_wsale_product_sub',

    init() {
        this._super(...arguments);
    },
    start() {
        this.$el.find('.product_price').css('direction', 'ltr');
        
        setTimeout(() => {
            document.querySelectorAll(".product_price .oe_currency_value").forEach(priceElement => {
                let priceText = priceElement.textContent.trim();
                let updatedPrice = priceText.replace(/(\.00)$/, ""); // Remove .00 if present
                priceElement.textContent = updatedPrice; // Update the element
            });
        }, 500);
        
        return this._super.apply(this, arguments);
    },
});

publicWidget.registry.ChangePriceDirectionProductPageSlider = publicWidget.Widget.extend({
    selector: '.s_dynamic_snippet_products',

    init() {
        this._super(...arguments);
    },
    start() {
        console.log("ChangePriceDirectionProductPageSlider");
        setTimeout(() => {
            console.log("called");
            document.querySelectorAll(".o_carousel_product_card_body .oe_currency_value").forEach(priceElement => {
                console.log("called inside");
                let priceText = priceElement.textContent.trim();
                let updatedPrice = priceText.replace(/(\.00)$/, ""); // Remove .00 if present
                priceElement.textContent = updatedPrice; // Update the element
            });
        }, 1000);

        return this._super.apply(this, arguments);
    },
});


publicWidget.registry.SliderHomePage = publicWidget.Widget.extend({
    selector: '.s_d_products_snippet',

    init() {
        this._super(...arguments);
    },
    start() {
        console.log("SliderHomePage");
        setTimeout(() => {
            document.querySelectorAll(".oe_currency_value").forEach(priceElement => {
                let priceText = priceElement.textContent.trim();
                let updatedPrice = priceText.replace(/(\.00)$/, ""); // Remove .00 if present
                priceElement.textContent = updatedPrice; // Update the element
            });
        }, 500);

        return this._super.apply(this, arguments);
    },
});


publicWidget.registry.CustomCurrencyWidget = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    start() {
        console.log(":white_check_mark: Custom JS widget initialized!");

        $(document).ready(function () {


            $('.oe_currency_value').each(function () {
                const originalText = $(this).text().trim().replace(/,/g, ''); // Remove commas
                const price = parseFloat(originalText);
        
                if (!isNaN(price)) {
                    if (price % 1 === 0) {
                        $(this).text(price.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }));
                    } else {
                        $(this).text(price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
                    }
                }
            });

            setTimeout(function () {

                // Loop through all .oe_currency_value elements
                $('.oe_currency_value').each(function () {
                    const originalText = $(this).text().trim().replace(/,/g, ''); // Remove commas
                    const price = parseFloat(originalText);
            
                    if (!isNaN(price)) {
                        if (price % 1 === 0) {
                            $(this).text(price.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }));
                        } else {
                            $(this).text(price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
                        }
                    }
                });
            }, 500); // Delay for 500ms
        });

        return this._super(...arguments);
    },
    remove_price: function () {

    }
});

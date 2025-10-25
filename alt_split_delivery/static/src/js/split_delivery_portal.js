/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SplitDeliveryAddress = publicWidget.Widget.extend({
    selector: '.split-delivery-form',

    start: function () {
        console.log('Split Delivery Address Widget Initialized');
        this._bindAddressSelectors();
        return this._super.apply(this, arguments);
        
    },

    _bindAddressSelectors: function () {
        console.log('Binding address selectors');
        const self = this;
        this.$('.address-selector').on('change', function () {
            console.log('Address selector changed:', this);
            const index = $(this).data('index');
            const selectedOption = this.options[this.selectedIndex];

            console.log('index:', index);
            console.log('Selected option:', selectedOption);

            const fields = ['street', 'street2', 'city', 'zip', 'country_id'];
            fields.forEach(function (field) {
                const $input = self.$(`[name='${field}_${index}']`);
                if (!$input.length) return;

                if (field === 'country_id') {
                    const countryName = selectedOption.dataset.country;
                    const $match = $input.find('option').filter(function () {
                        return $(this).text().trim() === countryName;
                    });
                    if ($match.length) {
                        $input.val($match.val());
                    }
                } else {
                    const value = selectedOption.dataset[field] || '';
                    $input.val(value);
                }
            });
        });
    },
});

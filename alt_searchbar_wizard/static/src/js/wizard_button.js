/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

console.log('📦 Alt Wizard On Off Button Working!');

publicWidget.registry.ButtonWizard = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click a[href="#search-wizard"]': '_onSearchWizardClick',
        'click #close_button': '_onClickClose',
        'click #reset_button': '_onClickReset',
    },

    start: function () {
        console.log('✅ ButtonWizard widget is running');
        //this._showWizardIfURLHasParams();
        return this._super.apply(this, arguments);
    },

    _onSearchWizardClick: function (ev) {
        ev.preventDefault();
        console.log('🚀 Search Wizard button clicked!');
        this._openSearchWizard();
    },

   _onClickClose: function () {
        const filter_div = $('#searchbar_wrapper');
        if (filter_div.length) {
            filter_div.stop(true, true).slideUp(); // Smooth close
        }
    },

    _onClickReset: function (ev) {
        ev.preventDefault();
        // window.location.href = '/shop';
        const wrapper = document.getElementById('searchbar_wrapper');
        if(wrapper){
            console.log("wrapper --------------- ",wrapper)
            const selects = wrapper.querySelectorAll('select');
            console.log("selects ----------------",selects)
            if(selects && selects.length > 0 ){
                selects.forEach(select =>{
                    console.log("select -----------------",select)
                    console.log("select -----------------",select.value)
                    select.value = '';  // Correctly reset to empty option
                })
            }

        }
    },

    _openSearchWizard: function () {
        const filter_div = $('#searchbar_wrapper');
        if (filter_div.length) {
            filter_div.stop(true, true).slideDown(); // Smooth open
        }
    },

    _showWizardIfURLHasParams: function () {
        const urlParams = new URLSearchParams(window.location.search);

        const keysToCheck = [
            'category',
            'attribute_value',
            'tags',
            'min_price',
            'max_price'
        ];

        const shouldShow = keysToCheck.some(key => urlParams.has(key));

        if (shouldShow) {
            console.log('🟢 Params detected in URL — showing search wizard');
            this._openSearchWizard();
        } else {
            console.log('🔵 No search-related params in URL');
        }
    }
});

return publicWidget.registry.ButtonWizard;

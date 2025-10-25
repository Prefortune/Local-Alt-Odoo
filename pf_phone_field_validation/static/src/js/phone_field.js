/** @odoo-module **/

import "@website/snippets/s_website_form/000";  // force deps
import publicWidget from "@web/legacy/js/public/public_widget";
import { session } from "@web/session";


publicWidget.registry.s_website_form.include({
    start: function () {
        this._super.apply(this, arguments); // original code runs

        console.log("Custom s_website_form widget started ---> ", this.el.querySelectorAll('input[type="tel"]'));

        // clear the auto-filled value if you don’t want it
        this.el.querySelectorAll('input[type="tel"]').forEach(telField => {
            if (telField.value === '+' + session.geoip_phone_code) {
                telField.value = '';  // remove Odoo’s auto-fill
            }
        });
    },
});


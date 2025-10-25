/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MobileMegaMenu = publicWidget.Widget.extend({
    selector: '#o_main_nav',

    start() {
        this._super(...arguments);
        if (window.innerWidth < 992) {   // only mobile/tablet
            this._removeCssArrows();
            this._bindMenuEvents();
        }
    },

    _removeCssArrows() {
        const style = document.createElement("style");
        style.innerHTML = `
        @media (max-width: 992px) {
            .tp-menu-sidebar ul > .nav-item > .dropdown-toggle::after {
                content: none !important;
                display: none !important;
            }
        }`;
        document.head.appendChild(style);
    },

    _bindMenuEvents() {
        console.log("-- _bindMenuEvents called --");

        this.$('a.nav-link.o_mega_menu_toggle').each(function () {
            const $parentLink = $(this);
            console.log(" --- $parentLink ------ ", $parentLink);

            const $submenu = $parentLink.siblings('.dropdown-menu');
            const targetUrl = $parentLink[0].getAttribute('data-url');;
            console.log(" --- targetUrl --- ", targetUrl);

            let $arrow = $parentLink.siblings('.mobile-submenu-arrow');
            if (!$arrow.length) {
                // const targetUrl = $parentLink.attr('href') || $parentLink.data('url') || '#';
                $arrow = $(`<a class="mobile-submenu-arrow ms-2" href="${targetUrl}">▸2</a>`);
                $parentLink.after($arrow);

            }


            // // Create arrow span if missing
            // let $arrow = $parentLink.find('.mobile-submenu-arrow');
            // if (!$arrow.length) {
            //     $arrow = $('<span class="mobile-submenu-arrow ms-2">▸1</span>');
            //     $parentLink.append($arrow);
            // }

        });
    },

});

export default publicWidget.registry.MobileMegaMenu;

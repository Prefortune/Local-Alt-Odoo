/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { hasTouch, isMobileOS } from "@web/core/browser/feature_detection";

publicWidget.registry.AltAdCart = publicWidget.Widget.extend({
    selector: '.oe_website_sale',

    // this code for ThemePrime
    // please read carefully all comments if you want to change anything in this flow 

    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.adslist = []
        this.mode = null
        this.interval = 4
        this.product_per_row = 4
    },

    willStart: async function () {

        this._super.apply(this, arguments);
        this.IsMobile = isMobileOS()
        this.url = window.location.href
        const ads = await rpc("/alt_ad_card/get_ads", {
            is_mobile: this.IsMobile,
        });
        if (ads && ads.length) {
            this.adslist = ads
        }
    },

    start: async function () {
        const urlObj = new URL(this.url);
        const params = urlObj.searchParams;
        const odoo_tags = params.getAll('tags');
        const view_mode = params.getAll('view_mode')[0] || 'grid';
        this.mode = view_mode;

        // if not theme prime then just uncomment below line and comment next below line 
        // const grid = document.querySelector("#o_wsale_products_grid");
        const grid = document.querySelector("#products_grid");
        const container = document.querySelector('.container.oe_website_sale.tp-shop-layout');
        if (container) {
            const shop_product_per_row = container.getAttribute('data-ppr');
            this.product_per_row = parseInt(shop_product_per_row);
            console.log(typeof this.product_per_row);
            console.log(this.product_per_row);
        } else {
            console.warn("No product grid container found on this page — skipping layout setup.");
            this.product_per_row = 4; // fallback default
        }
        // const shop_product_per_row = container.getAttribute('data-ppr');
        // this.product_per_row = parseInt(shop_product_per_row)
        // console.log( typeof this.product_per_row);
        // console.log(this.product_per_row);

        
        if (!grid) return;
        if (!this.adslist.length) return;

        // if not theme prime then just uncomment below line and comment next below line
        // const products = grid.querySelectorAll(".oe_product");
        const products = grid.querySelectorAll(".tp-product-item");
        
        if (!products.length) return;

        this.adslist.forEach((ad) => {
            const alt_category_ids = ad.category_ids
            const alt_tags_ids = ad.tags_ids
            const alt_position_type = ad.position_type
            const categoryHeader = document.querySelector("#category_header");
            const categoryId = categoryHeader?.getAttribute("data-oe-id");
            let alt_interval = ad.display_every || this.interval;
            this.product_per_row = this.IsMobile ? 2 : this.product_per_row;
            if(this.mode == 'grid' && alt_position_type === 'strip'){       
                alt_interval = alt_interval * this.product_per_row 
            }
            this.interval = alt_interval
            this.ShowAd(products, ad, alt_position_type, alt_category_ids, alt_tags_ids, categoryHeader, categoryId, odoo_tags)
        });
    },

    ArrayAreEqual: function (alt_tags_ids, odoo_tags) {
        const alt_tags_sorted = alt_tags_ids.map(String).sort();
        const odoo_tags_sorted = odoo_tags.sort();
        const SameTags = alt_tags_sorted.some(item => odoo_tags_sorted.includes(item));
        return SameTags
    },

    InsertAd: function (products, ad, classNames, step) {        
        for (let i = this.interval - 1; i < products.length; i += this.interval) {
            const adDiv = document.createElement("div");
            adDiv.setAttribute('data-ad', 'true');
            adDiv.classList.add(...classNames);
            adDiv.innerHTML = ad.html;
            const product = products[i];
            if (product && product.parentNode) {
                product.parentNode.insertBefore(adDiv, product.nextSibling);
            }
        }
    },

    ShowAd: function (products, ad, alt_position_type, alt_category_ids, alt_tags_ids, categoryHeader, categoryId, odoo_tags) {

        // add classNames name as per theme please set default class name oe_product and alt_ad_card for full width stripe
        var classNames = ["oe_product"];
        if (alt_position_type === 'strip') {
            classNames = ["oe_product", "alt_ad_card"]
        }
        if (alt_category_ids && categoryHeader) {

            if (alt_category_ids.includes(Number(categoryId))) {
                this.InsertAd(products, ad, classNames)
            }
        }
        else if (alt_tags_ids && odoo_tags) {
            const ShowAds = this.ArrayAreEqual(alt_tags_ids, odoo_tags)
            if (ShowAds) {
                this.InsertAd(products, ad, classNames)
            }
        }
        else if (!alt_category_ids && !alt_tags_ids) {
            this.InsertAd(products, ad, classNames)
        }
    },
    // destroy: function () {
    //     this._super.apply(this, arguments);
    // },
});

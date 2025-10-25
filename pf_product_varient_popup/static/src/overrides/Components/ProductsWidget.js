/** @odoo-module */

import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
import { patch } from "@web/core/utils/patch";
import { VariantPopup } from "@pf_product_varient_popup/app/popups/variant_popup/variant_popup"
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";


patch(ProductsWidget.prototype, { 
    get productsToDisplay() {
        let results;
        let tmpl_ids = {};
        console.log("this.searchWord:", this.searchWord);
        //console.log("productsToDisplay called | tagSearchActive:", this.pos.tagSearchActive);
        if (this.searchWord) {
            // search is active
            results = super.productsToDisplay;

            for (const product of results) {
                if (product.product_tmpl_id && product.qty_available > 0) {
                    tmpl_ids[product.product_tmpl_id] = product;
                }
            }

        } else {
            // Get all products from the POS database
            results = Object.values(this.pos.db.product_by_id);
            console.log(results);

            for (const product of results) {
                if (product.product_tmpl_id && product.qty_available > 0) {
                    tmpl_ids[product.product_tmpl_id] = product;
                }
                if (Object.keys(tmpl_ids).length > 100) {
                    break;
                }
            }
        }

        console.log("tmpl_ids Product:", Object.keys(tmpl_ids).length);

        return Object.values(tmpl_ids).sort((a, b) => 
            a.display_name.localeCompare(b.display_name)
        );
    },
    clickVariant:async function( product_tmpl_id ){
        var self = this;
        var varaint_ids = this.pos.db.product_by_tmpl_id[product_tmpl_id]
        var variants = []                   
        for (let varint_id of varaint_ids) {             
            if(varint_id.id){               
                let product = self.pos.db.product_by_id[varint_id.id]      
                if(product && product.qty_available > 0){
                    variants.push(product)
                }                    
            }               
        }
        await this.popup.add(VariantPopup, {
            title: _t("Product Variants"),
            product_variants: variants,            
        });
    
    }
})

// // Debounce helper
// function debounce(func, wait) {
//     let timeout;
//     return function (...args) {
//         clearTimeout(timeout);
//         timeout = setTimeout(() => func.apply(this, args), wait);
//     };
// }


// // Patch ProductScreen
// patch(ProductScreen.prototype, {
//     setup() {
//         super.setup();
//         this.pos = usePos();
//         //console.log("⚙️ ProductScreen setup called");
//         // Store the debounced handler
//         this.handleInputDebounced = debounce(this.handleInput.bind(this), 300);
//     },

//     async onMounted() {
//         await super.onMounted();
//         //console.log("🟢 ProductScreen onMounted called");

//         const findSearchInput = () => {
//             const selectors = [
//                 ".pos-search-bar input",
//                 ".o_searchbar_input",
//                 ".searchbar input",
//                 "input[type='text']",
//             ];
//             for (const selector of selectors) {
//                 const input = document.querySelector(selector);
//                 if (input) {
//                     //console.log(`🔍 Search input found with selector: ${selector}`);
//                     return input;
//                 }
//             }
//             //console.error("❌ Search input not found");
//             return null;
//         };

//         const searchInput = findSearchInput();
//         if (searchInput) {
//             searchInput.addEventListener("input", this.handleInputDebounced);
//             this.searchInput = searchInput;
//         } else {
//             this.observer = new MutationObserver(() => {
//                 const input = findSearchInput();
//                 if (input) {
//                     input.addEventListener("input", this.handleInputDebounced);
//                     this.searchInput = input;
//                     this.observer.disconnect();
//                     //console.log("⏳ Search input found via observer");
//                 }
//             });
//             this.observer.observe(document.body, { childList: true, subtree: true });
//         }
//     },

//     onWillUnmount() {
//         if (this.searchInput) {
//             this.searchInput.removeEventListener("input", this.handleInputDebounced);
//         }
//         if (this.observer) {
//             this.observer.disconnect();
//         }
//         //console.log("🟥 ProductScreen onWillUnmount called");
//     },

//     handleInput(event) {
//         const searchText = event.target.value.trim().toLowerCase();
//         //console.log("⌨️ Input event with text:", searchText);

//         if (!searchText) {
//             this.pos.tagSearchActive = false;
//         }else{
//             this.pos.tagSearchActive = true;
//         }

//          this.render(); // Trigger re-render
//     }
// });
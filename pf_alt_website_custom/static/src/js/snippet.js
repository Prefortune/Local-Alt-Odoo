import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.DynamicSnippet = publicWidget.Widget.extend({
   selector: '.dynamic_snippet',
   start: function () {
       var self = this;
       var data = jsonrpc('/product/list', {}).then((data) => {
        console.log('var data...........................................',data)
           self.$target.empty().append(data)
       });
   }
});

export default publicWidget.registry.DynamicSnippet;
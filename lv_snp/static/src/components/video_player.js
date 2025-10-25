/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.snpPlayerControl = publicWidget.Widget.extend({
    selector:'.lc-film-player',
    start:function (){
        this._super.apply(this,arguments)
        let self = this
        setTimeout(()=>{
            let widgets = self.$el.parent().parent().siblings("div.widget-visible")
            if (widgets.length){
                widgets.removeClass("widget-visible")
            }
        },3000)
    }

})

export default {
    snpPlayerControl:publicWidget.registry.snpPlayerControl
}

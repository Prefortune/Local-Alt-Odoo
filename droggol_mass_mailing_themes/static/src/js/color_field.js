/** @odoo-module **/

import { registry } from "@web/core/registry";
const { Component, useState, onMounted, useRef } = owl;

export class tpColorPicker extends Component {
    setup() {
        this.colors = useState(JSON.parse(this.props.record.data[this.props.name]));
        this.previewContainer = useRef('dr-color-container');
        onMounted(() => {
            $(this.previewContainer.el.querySelector('.d_mail_tooltip_1')).tooltip({
                delay: 0,
                html: true,
                title: "\
                        <div class='p-2'>\
                            <b class='bg-primary p-1'> <i class='fa fa-question-circle'></i> Help </b> \
                            <div class='mt-2'> • Choose your main brand color. </div> \
                            <div> • By default, all snippets will use this color. </div> \
                            <div> • You can also use it as a button, border, background or text color. </div> \
                        </div> \
                    "
            });
            $(this.previewContainer.el.querySelector('.d_mail_tooltip_2')).tooltip({
                delay: 0,
                html: true,
                title: "\
                        <div class='p-2'>\
                            <b class='bg-primary p-1'> <i class='fa fa-question-circle'></i> Help </b> \
                            <div class='mt-2'> • These are the extra colors in theme. </div> \
                            <div> •  You can use them as a background, border or text color. </div> \
                        </div> \
                    "
            });
            $(this.previewContainer.el.querySelector('.d_mail_tooltip_3')).tooltip({
                delay: 0,
                html: true,
                title: "\
                        <div class='p-2'>\
                            <b class='bg-primary p-1'> <i class='fa fa-question-circle'></i> Help </b> \
                            <div class='mt-2'> • The <i><b>header</b></i> color is used for title and headers e.g. H1, H2, H3...  </div> \
                            <div> •  The <i><b>content</b></i> color is used for all the text. </div> \
                            <div> •   Note: Dark colors are recommended for both. </div> \
                        </div> \
                    "
            });
        });
        super.setup();
    }
    _onColorChange(color, value) {
        this.colors[color] = value;
        let newVal = JSON.stringify(this.colors);
        this.props.record.update({[this.props.name]: newVal});
    }
}

tpColorPicker.template = "dr_color_palette_field";

export const TpColorPicker = {
    component: tpColorPicker,
    supportedTypes: ["char"],
};

registry.category("fields").add("d_field_color_palette", TpColorPicker);

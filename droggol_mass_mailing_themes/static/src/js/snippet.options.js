/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { renderToElement } from "@web/core/utils/render";
import { markup } from "@odoo/owl";

function _markUpValues(fieldNames, records) {
    records.forEach(record => {
        for (const fieldName of fieldNames) {
            if (record[fieldName]) {
                record[fieldName] = markup(record[fieldName]);
            }
        }
    });
    return records;
}

function insertBlocks(currentObj, widgetValue, RouteURL, priceList) {
    let selected_ids = []
    let template = currentObj.$target.attr('data-template');
    JSON.parse(widgetValue).forEach(function (item, index) {
        selected_ids.push(item.id);
    })
    currentObj.rpc(RouteURL, {
        domain : [['id', 'in', selected_ids]],
        pricelist_id : priceList ? priceList : false,
    }).then((data) => {
        currentObj.options.wysiwyg.odooEditor.observerUnactive('commitChanges');
        if (data.items.length && selected_ids && selected_ids.length){
            _markUpValues(['description', 'price', 'rating'], data.items);
            let result = [];
            selected_ids.forEach((id) => {
                let item = data.items.find(o => o.id === id);
                if (item) {
                    result.push(item);
                }
            });
            currentObj.$target.empty().append(renderToElement('droggol_mass_mailing_themes.' + template, {items:result}));
        } else {
            currentObj.$target.empty().append(renderToElement('droggol_mass_mailing_themes.s_d_select_records'));
        }
        currentObj.options.wysiwyg.odooEditor.observerActive('commitChanges');
    });
}

options.registry.d_mass_mailing_theme_option_module_status = options.Class.extend({

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },

    start: function () {
        var relatedApp = this.$target.data('relatedApp');
        var defs = [this._super.apply(this, arguments)];
        let selected_ids = this.$target.attr('data-selected-ids');
        this.options.wysiwyg.odooEditor.observerUnactive('commitChanges');
        if (!selected_ids){
            this.$target.empty().append(renderToElement('droggol_mass_mailing_themes.s_d_select_records'));
        }
        this.options.wysiwyg.odooEditor.observerActive('commitChanges');
        defs.push(this.orm.call("mailing.mailing", "dr_module_is_installed", [relatedApp]).then(((result) => {
            this.isModuleInstalled = result
            if (!this.isModuleInstalled) {
                this.dialog.add(ConfirmationDialog, {
                    title: _t('Can not Use'),
                    body: _t("To use this snippet you needs to install %s module.", relatedApp),
                    confirmClass: 'btn btn-primary',
                    confirm: () => {
                        this.trigger_up('remove_snippet', {
                            $snippet: this.$target,
                        });
                    },
                    cancel: () => {
                        this.trigger_up('remove_snippet', {
                            $snippet: this.$target,
                        });
                    },
                });
            }
        })));
        return Promise.all(defs);
    },

});

options.registry.d_mass_mailing_theme_option_products = options.Class.extend({

    init() {
        this._super(...arguments);
        this.pricelist = {};
        this.orm = this.bindService("orm");
        this.rpc = this.bindService("rpc");
    },

    _fetchPricelists: function () {
        return this.orm.searchRead("product.pricelist", [], ["id", "name"]);
    },

    _renderCustomXML: async function (uiFragment) {
        await this._super.apply(this, arguments);
        await this._renderPricelistSelector(uiFragment);
    },

    _renderPricelistSelector: async function (uiFragment) {
        if (!Object.keys(this.pricelist).length) {
            const pricelistList = await this._fetchPricelists();
            this.pricelist = {};
            for (let index in pricelistList) {
                this.pricelist[pricelistList[index].id] = pricelistList[index];
            }
        }
        const pricelistSelectorEl = uiFragment.querySelector('[data-name="dr_pricelist_opt"]');
        return this._renderSelectUserValueWidgetButtons(pricelistSelectorEl, this.pricelist);
    },

    _renderSelectUserValueWidgetButtons: async function (selectUserValueWidgetElement, data) {
        for (let id in data) {
            const button = document.createElement('we-button');
            button.dataset.selectDataAttribute = id;
            if (data[id].thumb) {
                button.dataset.img = data[id].thumb;
            } else {
                button.innerText = data[id].name;
            }
            selectUserValueWidgetElement.appendChild(button);
        }
    },

    _setOptionsDefaultValues: function () {
        this._setOptionValue('filterByPricelistId', -1);
        this._super.apply(this, arguments);
    },

    async selectDataAttribute(previewMode, widgetValue, params) {
        await this._super(...arguments);
        let changePlId = parseInt(this.$target.attr('data-filter-by-pricelist-id'));
        let priceList = changePlId !== -1 ? changePlId : false;
        if (params.name == 'dr_pricelist_opt') {
            let selected_ids = this.$target.attr('data-selected-ids');
            if (!selected_ids || selected_ids === '[]') {
                return false
            } else {
                widgetValue = this.$target.attr('data-selected-ids') || '[]';
            }
        }
        insertBlocks(this, widgetValue, '/droggol_mass_mailing_themes/get_products_info', priceList);
    },

});

options.registry.d_mass_mailing_theme_option_blogs = options.Class.extend({
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },

    async selectDataAttribute(previewMode, widgetValue, params) {
        await this._super(...arguments);
        insertBlocks(this, widgetValue, '/droggol_mass_mailing_themes/get_blogs_info');
    },
    
});

options.registry.d_mass_mailing_theme_option_event = options.Class.extend({
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },
    
    async selectDataAttribute(previewMode, widgetValue, params) {
        await this._super(...arguments);
        insertBlocks(this, widgetValue, '/droggol_mass_mailing_themes/get_events_info');
    },
    
});

options.registry.d_mass_mailing_theme_option_recruitment = options.Class.extend({
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },

    async selectDataAttribute(previewMode, widgetValue, params) {
        await this._super(...arguments);
        insertBlocks(this, widgetValue, '/droggol_mass_mailing_themes/get_recruitment_by_info');
    },

});

options.registry.d_mass_mailing_theme_option_elearning = options.Class.extend({
    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },

    async selectDataAttribute(previewMode, widgetValue, params) {
        await this._super(...arguments);
        insertBlocks(this, widgetValue, '/droggol_mass_mailing_themes/get_elearning_by_info');
    },

});

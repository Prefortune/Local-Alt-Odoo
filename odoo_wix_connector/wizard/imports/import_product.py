# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import api, models, _

from datetime import datetime

OdooType = [
    ('physical', 'consu'),
    ('digital', 'service'),  # digital
]

class ImportWixProducts(models.TransientModel):
    _name = "import.wix.products"
    _inherit = ['import.templates']
    _description = "Wix Products Import Wizard"

    def _import_wix_categories(self, channel_id, sdk, kwargs, obj):
        result = dict(
            mapping_ids=None,
            message=None
        )
        categ_import_res = obj.import_now(channel_id, sdk, {})
        s_ids, e_ids, feeds = self.env['category.feed'].with_context(
            channel_id=channel_id
        )._create_feeds(categ_import_res)
        return result

    @api.model
    def _wix_create_product_categories(self, channel_id, sdk, kwargs, category_ids):
        result = dict(
            res=False,
            import_res=False
        )
        feed_obj = self.env['category.feed']
        domain = [('store_id', 'in', list(set(category_ids)))]
        feed_exists = channel_id._match_feed(feed_obj, domain).mapped('store_id')
        category_ids = list(set(category_ids)-set(feed_exists))
        if len(category_ids):
            result['import_res'] = True
            obj = self.env['import.wix.categories']
            result['categ_import'] = self._import_wix_categories(
                channel_id, sdk, kwargs, obj)
        return result

    def _get_feed_variants(self, variation_ids):
        variant_list = []
        attribute_list = []
        quantity = 0
        for variant in variation_ids:
            if variant['choices']:
                attribute_list = [{
                    'name': attribute,
                    'value': option,
                } for attribute, option in variant['choices'].items()]
            quantity = variant.get('stock',{}).get('quantity', False)
            variant_list.append({
                'name_value': attribute_list,
                'store_id': variant['id'],
                'list_price': float(variant.get("variant").get("priceData").get("price")),
                'qty_available': quantity,
                'weight': variant.get('variant').get("weight"),
                'default_code': variant.get('variant').get('sku'),
            })
        return variant_list

    def get_wix_product_vals(
            self, sdk, channel_id,
            product_id, product_data,
            kwargs, attributes_list=None,
            configurable_product_options=None,
            trace_variant=False):
        attributes_list = attributes_list or dict()
        # configurable_product_options = configurable_product_options or list()
        type_id = product_data.get("productType")
        default_code = product_data.get('sku')
        vals = dict(
            store_id=product_id,
            channel_id=channel_id.id,
            extra_categ_ids = ','.join(product_data.get('collectionIds', [])),
            description_sale = product_data.get('description', ''),
            name = product_data.get('name'),
            default_code = default_code,
            variants = [],
        )
        if product_data.get('media', {}).get('mainMedia'):
            vals['image_url'] = product_data.get('media').get(
                'mainMedia').get('image', {}).get('url', False)
        if product_data.get('stock').get('trackInventory') and (not product_data.get("manageVariants")):
            vals['qty_available'] = int(
                product_data.get('stock').get('quantity')
            )
        # for product data in the case of the variants
        if product_data.get("manageVariants"):
            feed_variants = self._get_feed_variants(product_data["variants"])
            if feed_variants:
                vals['variants'] = feed_variants
        else:
            product_type = dict(OdooType).get(type_id, 'consu')
            vals.update(dict(
                type=product_type,
                is_storable = True if product_type == 'consu' else False,
                weight=product_data.get('weight'),
                list_price=product_data.get('price').get('price'),
            ))
        return vals

    def _wix_import_product(
            self, sdk, channel_id,
            product_id,
            product_data, kwargs):

        category_ids = product_data.get('collectionIds')
        if category_ids:
            categ_import = self._wix_create_product_categories(
                channel_id, sdk, kwargs, category_ids)
            if categ_import.get('import_res'):
                if categ_import.get('categ_import').get('mapping_ids'):
                    kwargs.update(
                        categ_imported=True,
                        ext_msg="New Categories got imported during product import! <br>"
                    )
                else:
                    kwargs.update(
                        ext_msg=categ_import.get(
                            'categ_import').get('message'),
                        categ_import=False
                    )
        vals = self.get_wix_product_vals(
            sdk, channel_id, product_id,
            product_data, kwargs)
        vals['store_id'] = product_id
        return vals

    def import_wix_products(
            self, sdk, channel_id, kwargs,
            type_id='configurable',
            condition_type='neq'):
        message = ''
        import_res = []
        current_page = kwargs.pop(
            'current_page') if kwargs.get('current_page') else 0
        kwargs['current_page'] = current_page
        if kwargs.get('filter_on') == "store_id" and kwargs.get('page_size') <= 1:
            # If page size(api record limit) is 1 then it was not evaluating because len(data_list) == page_size
            kwargs.update({'page_size': 2})
        if not kwargs.get("filter_on"):
            if channel_id.import_product_date:
                kwargs.update(
                    filter_on="date_range",
                    start_date=channel_id.import_product_date,
                    end_date=datetime.now()
                )
        fetch_data = channel_id._fetch_wix_product_data(
            sdk=sdk,
            type_id=type_id,
            condition_type=condition_type,
            **kwargs
        )
        if fetch_data:
            products = fetch_data.get('data').get('products', {}) or {}
            total_count = fetch_data.get('total_count')
            if kwargs.get('filter_on') in ["all", 'date_range'] or kwargs.get('from_cron'):
                kwargs = channel_id.wix_pagination(kwargs, total_count)
            if kwargs.get('from_cron'):
                dt_time = products[-1].get('createdDate').replace('T',
                                                                  ' ').split('.')[0]
                channel_id.import_product_date = dt_time
            msz = fetch_data.get('message', '')
            message += msz
            if products:
                message += fetch_data.get('message', '')
                import_res = list(map(lambda product: self._wix_import_product(sdk, channel_id, product.get('id'),
                                                       product, kwargs), products))
        return dict(
            res=import_res,
            msg=message,
            kwargs=kwargs
        )

    def _wix_import_products(self, sdk, channel_id, kwargs):
        data_list = []
        import_res = self.import_wix_products(sdk, channel_id,
                                                kwargs, type_id='configurable', condition_type='neq'
                                                )
        if import_res and import_res.get('res'):
            data_list = import_res.get('res')
        return data_list, kwargs

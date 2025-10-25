# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

from typing import Dict, List

from odoo import api, fields, models


class WebsiteTrackingService(models.Model):
    _inherit = "website.tracking.service"

    type = fields.Selection(selection_add=[('ga4', 'Google Analytics 4')], ondelete={'ga4': 'cascade'})
    ga4_debug_mode = fields.Boolean(string='Debug Mode')
    gtag_enhanced_conversions = fields.Boolean(string='Allow Enhanced Conversions', tracking=True)

    def _get_allowed_visitor_data(self) -> List[Dict]:
        self.ensure_one()
        res = super(WebsiteTrackingService, self)._get_allowed_visitor_data()
        res.append({'service': 'ga4', 'script': {'track_id_external'}, 'api': set()})
        return res

    @api.model
    def _get_google_types(self) -> List[str]:
        """ All Google tracking tag types. """
        return ['ga4']

    @api.model
    def _get_gtag_types(self) -> List[str]:
        """ Tracking tag types for the gtag.js script. """
        return ['ga4']

    def get_item_categories(self, product, property_name: str = 'content_category'):
        self.ensure_one()
        if self.type not in self._get_google_types():
            return super(WebsiteTrackingService, self).get_item_categories(product, property_name)
        res = {}
        if self.category_type == 'product':
            res.update({'item_category': product.categ_id.name})
        elif self.category_type == 'public':
            category = product.public_categ_ids and product.public_categ_ids[:1] or None
            if category:
                for index, category in enumerate(category.parents_and_self[:5]):
                    res.update({'item_category%s' % ((index + 1) if index > 0 else ''): category.name})
            else:
                res.update({'item_category': '-'})
        return res

    def get_common_data(self, event_type, product_data_list, order, pricelist):
        self.ensure_one()
        if self.type not in self._get_gtag_types():
            return super(WebsiteTrackingService, self).get_common_data(
                event_type=event_type,
                product_data_list=product_data_list,
                order=order,
                pricelist=pricelist,
            )
        currency = self.website_id._tracking_get_currency(order=order, pricelist=pricelist)
        data = {
            'send_to': self.key,
            'currency': currency.name,
        }
        return data

    def get_item_data_from_product_list(self, product_data_list, pricelist):
        self.ensure_one()
        if self.type not in self._get_google_types():
            return super(WebsiteTrackingService, self).get_item_data_from_product_list(
                product_data_list=product_data_list, pricelist=pricelist,
            )
        service = self
        website = service.website_id
        currency = website._tracking_get_currency(pricelist=pricelist)

        items = []
        total_value = 0
        for product_data in product_data_list:
            product = service.get_item(product_data)
            price = product_data.get('price', 0)
            qty = product_data.get('qty', 1)
            total_value += price * qty
            item_data = {
                'item_id': '%d' % product.id,
                'item_name': product.name,
                'price': float('%.2f' % price),
                'currency': currency.name,
                'quantity': qty,
            }
            item_data.update(service.get_item_categories(product))
            items.append(item_data)
        return {
            'value': float('%.2f' % total_value),
            'currency': currency.name,
            'items': items,
        }

    def get_item_data_from_order(self, order):
        self.ensure_one()
        if self.type not in self._get_google_types():
            return super(WebsiteTrackingService, self).get_item_data_from_order(order)
        service = self
        items = []
        for line in order.order_line:

            product = line.product_id
            if service.item_type == 'product.template':
                product = product.product_tmpl_id

            item_data = {
                'item_id': '%d' % product.id,
                'item_name': product.name,
                'price': float('%.2f' % service._get_final_product_price(line)),
                'currency': order.pricelist_id.currency_id.name,
                'quantity': line.product_uom_qty,
            }
            item_data.update(service.get_item_categories(product))
            items.append(item_data)
        items_data = {
            'items': items,
            'value': float('%.2f' % order.amount_total),
            'currency': order.pricelist_id.currency_id.name,
        }
        return items_data

    def get_data_for_login(self, product_data_list=None, pricelist=None, order=None):
        self.ensure_one()
        if self.type == 'ga4':
            return {'method': 'Odoo'}
        return super(WebsiteTrackingService, self).get_data_for_login(product_data_list, pricelist, order)

    def get_data_for_sign_up(self, product_data_list=None, pricelist=None, order=None):
        self.ensure_one()
        if self.type == 'ga4':
            return {'method': 'Odoo'}
        return super(WebsiteTrackingService, self).get_data_for_sign_up(product_data_list, pricelist, order)

    def get_data_for_search_product(self, product_data_list, pricelist, order):
        self.ensure_one()
        if self.type != 'ga4':
            return super(WebsiteTrackingService, self).get_data_for_search_product(
                product_data_list=product_data_list, pricelist=pricelist, order=order,
            )
        return {'search_term': self._context.get('search_term', '')}

    def get_data_for_add_payment_info(self, product_data_list=None, pricelist=None, order=None):
        self.ensure_one()
        data = super(WebsiteTrackingService, self).get_data_for_add_payment_info(
            product_data_list=product_data_list, pricelist=pricelist, order=order,
        )
        if self.type not in self._get_google_types():
            return data
        payment_provider = self.env['payment.provider'].browse(self._context.get('payment_provider_id', 0))
        if payment_provider:
            data.update({'payment_type': payment_provider.name})
        return data

    def get_data_for_purchase(self, product_data_list, pricelist, order):
        self.ensure_one()
        data = super(WebsiteTrackingService, self).get_data_for_purchase(
            product_data_list=product_data_list,
            pricelist=pricelist,
            order=order,
        )
        if self.type in self._get_google_types():
            data.update({
                'transaction_id': order.name,
                'tax': order.amount_tax,
            })
        return data

    def complete_user_data(self, user_data: Dict) -> Dict:
        self.ensure_one()
        if self.type not in self._get_google_types():
            return super(WebsiteTrackingService, self).complete_user_data(user_data)

        user_vals = {'address': {}}
        address_fields = [
            'first_name', 'sha256_first_name', 'last_name', 'sha256_last_name',
            'street', 'sha256_street', 'city', 'postal_code', 'region', 'country',
        ]
        for address_field in address_fields:
            address_value = user_data.get(address_field)
            if address_value:
                user_vals['address'][address_field] = address_value

        contact_fields = ['email', 'sha256_email_address', 'phone_number', 'sha256_phone_number']
        for contact_field in contact_fields:
            contact_value = user_data.get(contact_field)
            if contact_value:
                user_vals[contact_field] = contact_value

        return user_vals

    @api.model
    def _get_privacy_url(self):
        urls = super(WebsiteTrackingService, self)._get_privacy_url()
        urls.update({'ga4': 'https://developers.google.com/analytics/devguides/collection/protocol/ga4/policy'})
        return urls

    def _visitor_data_mapping(self) -> Dict[str, Dict]:
        self.ensure_one()
        if self.type not in self._get_google_types():
            return super(WebsiteTrackingService, self)._visitor_data_mapping()
        # flake8: noqa: E501
        return {
            'first_name': {'name': 'first_name', 'hash': True, 'name_hashed_alias': 'sha256_first_name'},
            'last_name': {'name': 'last_name', 'hash': True, 'name_hashed_alias': 'sha256_last_name'},
            'email': {'name': 'email', 'hash': True, 'name_hashed_alias': 'sha256_email_address'},
            'phone':  {'name': 'phone_number', 'remove_plus': False, 'hash': True, 'name_hashed_alias': 'sha256_phone_number'},
            'street':  {'name': 'street', 'hash': False, 'name_hashed_alias': 'sha256_street'},
            'city':  {'name': 'city', 'hash': False},
            'zip':  {'name': 'postal_code', 'hash': False},
            'state':  {'name': 'region', 'hash': False},
            'country': {'name': 'country', 'hash': False},
        }

    @api.model
    def _fields_to_invalidate_cache(self) -> List[str]:
        return super(WebsiteTrackingService, self)._fields_to_invalidate_cache() + [
            'ga4_debug_mode', 'gtag_enhanced_conversions',
        ]

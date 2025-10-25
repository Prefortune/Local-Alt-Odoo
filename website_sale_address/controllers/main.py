# Copyright © 2020 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License OPL-1 (https://www.odoo.com/documentation/14.0/legal/licenses.html#odoo-apps).

import logging
from typing import Set, Dict, List

from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale


_logger = logging.getLogger(__name__)


class WebsiteSaleExtend(WebsiteSale):

    @route()
    def shop_country_info(self, country, address_type, **kw):
        """Override method for route /shop/country_info/<country_id>"""
        result: Dict = super().shop_country_info(country, address_type, **kw)
        website = request.website.sudo()
        # Remove from list field names (not allowed to show by website options)
        # that can be displayed from JS (public widget websiteSaleAddress._changeCountry)
        # NOTE: it can be changed with Odoo updates
        fields_to_check = []
        fields_to_remove = set()
        field_names: List = result['fields']
        if address_type == 'billing':
            fields_to_check += [
                (not website.use_billing_address_street, 'street'),
                (not website.use_billing_address_zip, 'zip'),
                (not website.use_billing_address_city, 'city'),
            ]

        else:  # means address_type is 'delivery'
            fields_to_check += [
                (not website.use_shipping_address_street, 'street'),
                (not website.use_shipping_address_zip, 'zip'),
                (not website.use_shipping_address_city, 'city'),
            ]

        for condition, field in fields_to_check:
            if condition:
                fields_to_remove.add(field)

        result['fields'] = list(set(field_names) - fields_to_remove)

        return result

    def _prepare_address_form_values(
        self, order_sudo, partner_sudo, address_type, use_delivery_as_billing, callback='', **kwargs
    ):
        result: Dict = super()._prepare_address_form_values(
            order_sudo, partner_sudo, address_type, use_delivery_as_billing, callback, **kwargs)
        mode = 'new' if result['is_anonymous_cart'] else 'edit'
        default_billing_country = request.website.default_billing_country_id
        default_shipping_country = request.website.default_shipping_country_id

        if all([
            default_billing_country,
            address_type == 'billing',
            (mode == 'new' or not result['country']),
        ]):
            result.update({
                'country': default_billing_country
            })
            if mode == 'edit':
                order_sudo.partner_id.country_id = default_billing_country.id

        if all([
            default_shipping_country,
            address_type == 'delivery',
            (mode == 'new' or not result['country']),
        ]):
            result.update({
                'country': default_shipping_country,
                'country_states': default_shipping_country.state_ids,
            })
            if order_sudo.partner_id != order_sudo.partner_shipping_id:
                order_sudo.partner_shipping_id.country_id = default_shipping_country.id

        return result

    def _get_mandatory_billing_address_fields(self, country_sudo):
        """ Change original field set for website billing address:
        {
            "name", "phone", "email", "street", "city", "country_id",
            "state_id" (optional), "zip" (optional)
        }.
        """
        field_names: Set = super()._get_mandatory_billing_address_fields(country_sudo)
        website = request.website.sudo()
        # Remove standard required fields
        if (
            not website.use_billing_address_street
            or website.use_billing_address_street and not website.billing_address_street_required
        ):
            field_names.discard('street')
        if (
            not website.use_billing_address_city
            or website.use_billing_address_city and not website.billing_address_city_required
        ):
            field_names.discard('city')
        if (
            not website.use_billing_address_phone
            or website.use_billing_address_phone and not website.billing_address_phone_required
        ):
            field_names.discard('phone')

        # Country related fields
        if website.billing_address_zip_required:
            field_names.add('zip')
        else:
            field_names.discard('zip')
        if website.billing_address_state_required:
            field_names.add('state_id')
        else:
            field_names.discard('state_id')

        # Set custom required fields
        if website.use_billing_address_street2 and website.billing_address_street2_required:
            field_names.add('street2')

        return field_names

    def _get_mandatory_delivery_address_fields(self, country_sudo):
        """ Change original field set for website delivery (shipping) address:
        {
            "name", "phone", "email", "street", "city", "country_id",
            "state_id" (optional), "zip" (optional)
        }.
        """
        field_names: Set = super()._get_mandatory_delivery_address_fields(country_sudo)
        website = request.website.sudo()

        # Remove standard required fields
        if (
            not website.use_shipping_address_street
            or website.use_shipping_address_street and not website.shipping_address_street_required
        ):
            field_names.discard('street')

        if (
            not website.use_shipping_address_city
            or website.use_shipping_address_city and not website.shipping_address_city_required
        ):
            field_names.discard('city')

        if (
            not website.use_shipping_address_phone
            or website.use_shipping_address_phone and not website.shipping_address_phone_required
        ):
            field_names.discard('phone')

        # Country related fields
        if website.shipping_address_zip_required:
            field_names.add('zip')
        else:
            field_names.discard('zip')
        if website.shipping_address_state_required:
            field_names.add('state_id')
        else:
            field_names.discard('state_id')

        # Set custom required fields
        if website.use_shipping_address_street2 and website.shipping_address_street2_required:
            field_names.add('street2')

        return field_names

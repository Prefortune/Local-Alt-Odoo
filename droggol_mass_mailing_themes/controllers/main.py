# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present Droggol Infotech Private Limited. (<https://www.droggol.com/>)

import json

from odoo import http, fields
from odoo.http import request

import babel

from odoo.tools import posix_to_ldml


class DroggolMassMailingThemes(http.Controller):

    def _get_events(self, domain):
        lang = request.env.user.lang
        is_website_event = request.env['mailing.mailing'].dr_module_is_installed('website_event')
        fields_list = ['name', 'organizer_id', 'date_begin', 'date_end', 'address_id', 'event_type_id']
        if is_website_event:
            fields_list.append('website_url')
        events = request.env['event.event'].with_context(lang=lang).search(domain)
        result = events.read(fields_list)
        for res_event, event in zip(result, events):
            res_event['start_month'] = res_event.get('date_begin').strftime('%b')
            res_event['start_year'] = res_event.get('date_begin').strftime('%Y')
            res_event['start_day'] = res_event.get('date_begin').strftime('%d')

            res_event['date_begin'] = self.format_user_lang(res_event.get('date_begin'))
            res_event['date_end'] = self.format_user_lang(res_event.get('date_end'))
            if res_event.get('event_type_id'):
                res_event['event_type'] = res_event.get('event_type_id')[1]
            if res_event.get('organizer_id'):
                res_event['organizer_name'] = res_event.get('organizer_id')[1]
            if event.address_id.country_id:
                res_event['country_name'] = event.address_id.country_id.name
                res_event['street'] = event.address_id.street
                res_event['address'] = event.address_id.name
            if is_website_event:
                cover_properties = json.loads(event.cover_properties)
                res_event['cover_img'] = cover_properties.get('background-image', 'none')[4:-1].strip("'")
        return result

    def format_user_lang(self, value):
        if not value:
            return ''

        lang_code = request.env.user._context.get('lang') or 'en_US'
        lang = request.env['res.lang']._lang_get(lang_code)
        locale = babel.Locale.parse(lang.code)

        value = fields.Datetime.from_string(value)
        value = fields.Datetime.context_timestamp(request.env.user, value)
        strftime_pattern = (u"%s %s" % (lang.date_format, lang.time_format))
        pattern = posix_to_ldml(strftime_pattern, locale=locale)
        pattern = pattern.replace(":ss", "").replace(":s", "")
        return babel.dates.format_datetime(value, format=pattern, locale=locale)

    @http.route('/droggol_mass_mailing_themes/get_events_info', type='json', auth='public', website=True)
    def get_events_info(self, domain):
        return {
            'items': self._get_events(domain)
        }

    def _get_blogs(self, domain):
        lang = request.env.user.lang
        blogs = request.env['blog.post'].with_context(lang=lang).search(domain)
        result = blogs.read(['name', 'author_id', 'website_url', 'teaser', 'post_date', 'visits'])
        for res_blog, blog in zip(result, blogs):
            cover_properties = json.loads(blog.cover_properties)
            res_blog['blog_img'] = cover_properties.get('background-image', 'none')[4:-1].strip("'")
            if res_blog.get('author_id'):
                res_blog['author_img'] = '/web/image/blog.post/'+str(res_blog.get('author_id')[0])+'/author_avatar'
                res_blog['author_name'] = res_blog.get('author_id')[1]
                res_blog['post_date'] = res_blog.get('post_date').strftime('%b-%Y')
        return result

    @http.route('/droggol_mass_mailing_themes/get_blogs_info', type='json', auth='public', website=True)
    def get_blogs_info(self, domain):
        return {
            'items': self._get_blogs(domain)
        }

    def _get_recruitment(self, domain):
        lang = request.env.user.lang
        is_website_recruitment = request.env['mailing.mailing'].dr_module_is_installed('website_hr_recruitment')
        fields_list = ['name', 'no_of_recruitment', 'description']
        if is_website_recruitment:
            fields_list.append('website_url')
        recruitments = request.env['hr.job'].with_context(lang=lang).search(domain)
        result = recruitments.read(fields_list)
        return result

    @http.route('/droggol_mass_mailing_themes/get_recruitment_by_info', type='json', auth='public', website=True)
    def get_recruitment_by_info(self, domain):
        return {
            'items': self._get_recruitment(domain)
        }

    def _get_elearning(self, domain):
        lang = request.env.user.lang
        elearning = request.env['slide.channel'].with_context(lang=lang).search(domain)
        result = elearning.read(['name', 'website_url', 'description', 'total_time'])
        for res in result:
            time = int(res['total_time'])
            time_diff = res['total_time'] - int(res['total_time'])
            res['total_time'] = '' if (time == 0) and (time_diff == 0) else str(time) + ' hours ' + str(int((60 * time_diff ))) + ' minutes'
        return result

    @http.route('/droggol_mass_mailing_themes/get_elearning_by_info', type='json', auth='public', website=True)
    def get_elearning_by_info(self, domain):
        return {
            'items': self._get_elearning(domain)
        }

    def _get_produts_fields(self):
        fields_to_fetch = ['id', 'name', 'display_name', 'list_price','description_sale', 'default_code']
        if request.env['mailing.mailing'].dr_module_is_installed('website_sale'):
            fields_to_fetch.extend(['website_url', 'is_published'])
        return fields_to_fetch

    def _get_rating_template(self, rating_avg, rating_count=False):
        return request.env['ir.ui.view']._render_template('droggol_mass_mailing_themes.dr_rating_widget_stars_static', values={
            'rating_avg': rating_avg,
            'rating_count': rating_count,
        })

    def get_products(self, domain, pricelist_id=None):
        lang = request.env.user.lang
        PriceListModel = request.env['product.pricelist']
        if pricelist_id:
            pricelist = PriceListModel.browse(pricelist_id)
        else:
            pricelist = PriceListModel.search([], limit=1)
        Model = request.env['product.template'].with_context(pricelist=pricelist.id)
        products = Model.with_context(lang=lang).search(domain)
        fields_to_fetch = self._get_produts_fields()
        products_data = products.read(fields_to_fetch)
        FieldMonetary = request.env['ir.qweb.field.monetary']
        monetary_options = {
            'display_currency': pricelist.currency_id or request.env['res.company'].search([], limit=1).currency_id,
        }
        is_rating_active = False
        if request.env['mailing.mailing'].dr_module_is_installed('website_sale'):
            is_rating_active = request.website.viewref('website_sale.product_comment').active

        for res_product, product in zip(products_data, products):
            combination_info = {}
            price = product.with_context(pricelist=pricelist.id)._get_contextual_price()
            res_product.update(combination_info)
            res_product['price'] = FieldMonetary.value_to_html(price, monetary_options)
            description = res_product.get('description_sale')
            if description and len(description) > 180:
                res_product['description_sale'] = description[:180] + '...'
            elif description:
                res_product['description_sale'] = description
            else:
                res_product['description_sale'] = ''
            if is_rating_active:
                res_product['rating'] = self._get_rating_template(product.rating_avg, product.rating_count)
            if 'website_url' in fields_to_fetch and not res_product.get('is_published'):
                res_product.pop('website_url', None)
        return products_data

    @http.route('/droggol_mass_mailing_themes/get_products_info', type='json', auth='public', website=True)
    def get_snippet_product_info(self, domain, pricelist_id=None):
        return {
            'items': self.get_products(domain, pricelist_id=pricelist_id),
        }

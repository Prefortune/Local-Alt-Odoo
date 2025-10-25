from odoo import http,_
from odoo.http import request , route
import json
import logging
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)
from odoo.tools import str2bool , clean_context

from odoo.addons.website_sale.controllers.delivery import Delivery

# from odoo.addons.website_sale.controllers.main import WebsiteSale

# class WebsiteSaleInherit(WebsiteSale):

#     @http.route(['/shop/confirm_order'], type='http', auth="public", website=True, sitemap=False)
#     def shop_confirm_order(self, **post):
#         _logger.info("shop/confirm_order is caled --------------------------------------- %s",post)
#         order_sudo = request.website.sale_get_order()

#         if order_sudo:
#             gretting_note = ''
#             delivery_note = ''

#             if post['split_delivery_note_input']:
#                 gretting_note = post['split_greeting_card_input']
#             if post['split_delivery_note_input']:
#                 delivery_note = post['split_delivery_note_input']

#             order_sudo.greeting_card = gretting_note
#             order_sudo.delivery_note = delivery_note

#         if redirection := self._check_cart_and_addresses(order_sudo):
#             return redirection

#         order_sudo._recompute_taxes()
#         order_sudo._recompute_prices()
#         extra_step = request.website.viewref('website_sale.extra_info')
#         if extra_step.active:
#             return request.redirect("/shop/extra_info")

#         return request.redirect("/shop/payment")

class DeliveryController(http.Controller):

    @http.route('/get/current/split_qty', type='json', auth='public', website=True)
    def get_current_split_qty(self):
        order = request.website.sale_get_order()
        _logger.info("order is getting with split qty of ---- %s , %s",order , order.alt_split_delivery_count)
        if order:
            return {
                'split_qty': order.alt_split_delivery_count or 1,
            }
        return {'split_qty': 1}

    @http.route('/get/schedule/date', type='json', auth='public', website=True)
    def get_schedule_date_(self):
        order = request.website.sale_get_order()
        if order:
            data = {}
            if order.customer_delivery_date:
                data['schedule_date'] = order.customer_delivery_date
                data['status'] = True
            else:
                data['schedule_date'] = False
                data['status'] = False
            return data
        return {
            'status' : False
        }
    
    @http.route('/get/notes', type='json', auth='public', website=True)
    def get_notes_from_order(self):
        order = request.website.sale_get_order()
        if order:
            data = {}
            if order.greeting_card:
                data['greeting_card'] = order.greeting_card
            if order.delivery_note:
                data['delivery_note'] = order.delivery_note
            return data
        return {
            'greeting_card' : False,
            'delivery_note' : False
        }


class WebsiteSaleCustom(http.Controller):
    @http.route(['/shop/set_delivery_date'], type='json', auth='public', website=True)
    def set_delivery_date(self, delivery_date=None):
        order = request.website.sale_get_order()
        if order:
            if not delivery_date:
                order.customer_delivery_date = False  # Clear the field
            else:
                order.customer_delivery_date = delivery_date  # Set new value
            return {'success': True, 'order_id': order.id}
        return {'success': False}

    @http.route(['/shop/set_gretting_note'], type='json', auth='public', website=True)
    def set_gretting_note(self, gretting_note=None):
        order = request.website.sale_get_order()
        _logger.info("gretting_note --- %s",gretting_note)
        if order:
            if not gretting_note:
                order.greeting_card = False  # Clear the field
            else:
                order.greeting_card = gretting_note  # Set new value
            return {'success': True, 'order_id': order.id}
        return {'success': False}

    @http.route(['/shop/set_delivery_note'], type='json', auth='public', website=True)
    def set_delivery_note(self, delivery_note=None):
        order = request.website.sale_get_order()
        _logger.info("delivery_note --- %s",delivery_note)
        if order:
            if not delivery_note:
                order.delivery_note = False  # Clear the field
            else:
                order.delivery_note = delivery_note  # Set new value
            return {'success': True, 'order_id': order.id}
        return {'success': False}
    
    

class DeliveryInherit(Delivery):
    @route('/shop/set_delivery_method', type='json', auth='public', website=True)
    def shop_set_delivery_method(self, dm_id=None, split_qty=None, **kwargs):
        _logger.info("shop_set_delivery_method called with dm_id: %s", dm_id)
        """ Set the delivery method on the current order and return the order summary values.

        If the delivery method is already set, the order summary values are returned immediately.

        :param str dm_id: The delivery method to set, as a `delivery.carrier` id.
        :param dict kwargs: The keyword arguments forwarded to `_order_summary_values`.
        :return: The order summary values, if any.
        :rtype: dict
        """
        _logger.info("shop_set_delivery_method called with dm_id: %s, split_qty: %s", dm_id, split_qty)
        order_sudo = request.website.sale_get_order()
        _logger.info("Current order: %s %s", order_sudo,order_sudo.name)
        order_sudo.alt_split_delivery_count = int(split_qty) if split_qty else 0

        # if order_sudo.carrier_id:
        #     carrier = order_sudo.carrier_id
        #     if carrier.supports_split_delivery:
        #         _logger.info("Carrier supports split delivery %s", carrier.name)
        #         product = carrier.product_id
        #         if product:
        #             _logger.info("Carrier %s has product %s", carrier.name, product.name)
        #             for line in order_sudo.order_line:
        #                 _logger.info("Updating delivery line %s with rate %s", line.name, split_qty)
        #                 if split_qty:
        #                     line.name = f'{line.name} - {split_qty}'


        if not order_sudo:
            return {}

        dm_id = int(dm_id)
        # if dm_id != order_sudo.carrier_id.id:
        for tx_sudo in order_sudo.transaction_ids:
            if tx_sudo.state not in ('draft', 'cancel', 'error'):
                raise UserError(_(
                    "It seems that there is already a transaction for your order; you can't"
                    " change the delivery method anymore."
                ))

        delivery_method_sudo = request.env['delivery.carrier'].sudo().browse(dm_id).exists()
        is_split = delivery_method_sudo.supports_split_delivery
        _logger.info("---is_split------ %s",is_split)
        _logger.info("---delivery_method_sudo------ %s",delivery_method_sudo)
        order_sudo._set_delivery_method(delivery_method_sudo)
        return self._order_summary_values(order_sudo, **kwargs)

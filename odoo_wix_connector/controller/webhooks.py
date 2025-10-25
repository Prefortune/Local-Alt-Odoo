# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import http, SUPERUSER_ID
from odoo.http import request
from ..tools.help import jwt_Token
from logging import getLogger
_logger = getLogger(__name__)

# ========================== "Wix Store" Webhooks ===========================
class WixWebhook(http.Controller):

# Note: Sometimes webhook triggers more than once
    # New product created on wix end will import it in real time
    # Need All permissions regarding products read-write
    @http.route(['/wix/product_new/<string:id>'], type = "http", auth = "public", csrf = False)
    def product_created(self, id, **kw):
        try:
            channel_id = request.env['multi.channel.sale'].sudo().search([('channel','=','wix'),('id','=',id),('active','=',True)],limit = 1)
            if channel_id and channel_id.wix_product_create_webhook_enable:
                event = request.httprequest.data
                jwt_data={"token":event}
                response= jwt_Token(jwt_data, channel_id)
                if response:
                    data = response.get('data')
                    product_id = data.get('productId')
                    domain = [('store_id','=',product_id)]
                    feed_obj = request.env['product.feed']
                    feed_status = channel_id._match_feed(feed_obj, domain, 1)
                    if not feed_status:
                        self.import_data_by_id("product.template", channel_id, product_id)
                        return request.redirect('Success')
            else:
                _logger.warning('Wix channel or Product Created Webhook is not active')
        except Exception as e:
            _logger.error('Exception occurred in Product Created Webhook %r',e, exc_info=True)
        return request.redirect('No Webhook Response')

    # Webhook for New Order in wix permission(Manage orders or Read orders)
    @http.route(['/wix/order_new/<string:id>'],type = "http", auth = "public", csrf = False)
    def order_new(self, id, **kw):
        try:
            channel_id = request.env['multi.channel.sale'].sudo().search([('channel','=','wix'),('id','=',id),('active','=',True)],limit = 1)
            if channel_id and channel_id.wix_order_webhook_enable:
                event = request.httprequest.data
                jwt_data={"token":event}
                response= jwt_Token(jwt_data, channel_id)
                if response:
                    data = response.get('data')
                    order_id = data.get('orderId')
                    domain = [('store_id','=',order_id)]
                    feed_obj = request.env['order.feed']
                    feed_status = channel_id._match_feed(feed_obj, domain, 1)
                    if not feed_status:
                        self.import_data_by_id("sale.order", channel_id, order_id)
                        return request.redirect('Success')
            else:
                _logger.info('Wix channel or Order Webhook is not active')
        except Exception as e:
            _logger.info('Exception occurred in Wix Order Webhook %r',e, exc_info=True)
        return request.redirect('No Webhook Response')

    @http.route(['/wix/order_cancel/<string:id>'], type = "http", auth = "public", csrf = False)
    def order_cancel(self, id, **kw):
        try:
            channel_id = request.env['multi.channel.sale'].sudo().search([('channel','=','wix'),('id','=',id),('active','=',True)],limit = 1)
            if channel_id and channel_id.wix_order_cancel_webhook_enable:
                event = request.httprequest.data
                jwt_data={"token":event}
                response= jwt_Token(jwt_data,channel_id)
                if response:
                    data = response.get('data').get('order')
                    order_id = data.get('id')
                    if order_id:
                        self.cancel_order_in_odoo(order_id, channel_id)
                        return request.redirect('Success')
            else:
                _logger.info('Wix channel or Order Cancelled Webhook is not active ')
        except Exception as e:
            _logger.error('Exception occurred in Wix Order Cancel Webhook %r',e, exc_info=True)
        return request.redirect('No Webhook Response')


    # It will change the order_state to cancel in order feed and change the state to draft
    def cancel_order_in_odoo(self, id, channel_id):
        cancel_state = "CANCELED"
        order_feed = request.env['order.feed'].sudo().search([('channel','=','wix'),('channel_id','=',channel_id.id),('store_id','=',id)],limit=1)
        if order_feed:
            order_state = order_feed.order_state
            if order_state:
                order_state = order_state.split(',')
                order_state[1] = cancel_state
                # Comma seperated order state "payment_state,fullfillment_state"
                order_state = ",".join(order_state).strip()
            order_feed.write({'state':'draft','order_state':order_state})
            if channel_id.auto_evaluate_feed:
                order_feed.sudo().import_items()
        # +++++++++++++ OR +++++++++++++++
        # match = request.env['channel.order.mappings'].search([('ecom_store','=','wix'),('channel_id','=',channel_id.id),('store_order_id','=',id)])
        # if match:
        #     match.order_name.sudo().action_cancel()

    def import_data_by_id(self, model, channel, id):
        kw = dict(
            filter_on = "store_id",
            store_id = id,
            object = model,
            from_webhook = True
        )
        request.env["import.operation"].with_user(SUPERUSER_ID).create({
            "channel_id":channel.id,
            }).import_with_filter(**kw)

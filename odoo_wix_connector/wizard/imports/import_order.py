# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from datetime import datetime
from logging import getLogger
_logger = getLogger(__name__)

from odoo import models, _

class ImportWixOrders(models.TransientModel):
    _name = 'import.wix.orders'
    _inherit = 'import.orders'
    _description = "Import Wix Orders"
    
    def create_product_feed(self, sdk, channel_id, remote_id):
        if remote_id:
            if not channel_id.match_product_feeds(remote_id):
                kwargs={
                    'filter_on':"store_id",
                    'store_id':remote_id, 
                    'page_size':channel_id.api_record_limit
                    }
                product_data, kwargs = self.env['import.wix.products']._wix_import_products(sdk, channel_id, kwargs)
                if product_data:
                    vals = product_data[0]
                    feed_variants = vals.pop('variants', [])
                    if feed_variants:
                        feed_variants = [(0, 0, variant) for variant in feed_variants]
                    vals.update(feed_variants=feed_variants)
                    self.env['product.feed'].create([vals])

    def _wix_import_orders(self,sdk,channel_id, kwargs):
        current_page = kwargs.pop('current_page') if kwargs.get('current_page') else 0
        kwargs.update({'current_page':current_page})
        fetch_data=channel_id._fetch_wix_order_data(sdk, **kwargs)
        data_list = []
        items=[]
        if not fetch_data.get('data'):
            return data_list, kwargs
        orders = fetch_data.get('data').get('orders')
        total_count = 0
        if fetch_data.get('data').get('metadata'):
            total_count = fetch_data.get('data').get('metadata').get('count')
        if kwargs.get('filter_on') in ['all','date_range','order_state'] or kwargs.get('from_cron'):#not kwargs.get('from_webhook') or kwargs.get('filter_on') != "store_id":
            if fetch_data.get('data').get('metadata' ,{}).get('hasNext'):
                kwargs.update({'wix_next_url': fetch_data.get('data').get('metadata').get('cursors',{}).get('next')})
            kwargs = channel_id.wix_pagination(kwargs, total_count)
        payment_methods, order_ids = {}, []
        for order in orders:
            if order.get('paymentStatus') == 'PAID':
                order_ids.append(order.get('id'))
        if order_ids:
            payment_methods = self.get_order_transaction(sdk, order_ids) # Get payment methods in bulk
        for order in orders:
            orders_data=self._process_order(sdk, channel_id, order)
            if payment_methods.get(order.get('id')):
                orders_data['payment_method'] = payment_methods.get(order.get('id'))
            data_list.append(orders_data)
        if kwargs.get('from_cron'):
            if orders:
                dateCreated = orders[-1].get('createdDate').replace('T',' ').split('.')[0]
                channel_id.import_order_date = datetime.strptime(dateCreated,"%Y-%m-%d %H:%M:%S")
        return data_list, kwargs

    def _get_wix_discount_lines(self, sdk, data,channel_id):
        discount_amount = float(data.get('priceSummary').get('discount').get('amount'))
        vals = {
            'line_name': "Discount",
            'line_price_unit': float(discount_amount),
            'line_product_uom_qty': 1,
            "line_source":"discount",
        }
        return vals

    def _get_wix_order_line(self, sdk, channel_id, data):
        order_lines = []
        tax_list = []
        for line in data.get("lineItems"):
            product_id, store_variant_id = line.get('catalogReference', {}).get('catalogItemId', False), False
            if line.get('catalogReference' ,{}).get('options'):
                store_variant_id=line.get('catalogReference').get('options').get('variantId')
            if store_variant_id == '00000000-0000-0000-0000-000000000000':
                store_variant_id = False
            match = channel_id.match_product_mappings(product_id, store_variant_id)
            if not match: # create product feed
                self.create_product_feed(sdk, channel_id, product_id)
            line_taxes = self.wix_get_tax_line(channel_id, line)
            if not tax_list:
                tax_list = line_taxes
            order_line_dict = {
                'line_name': line.get('productName').get('original'),
                'line_price_unit': float(line.get('price').get('amount')),
                'line_product_uom_qty': line.get('quantity'),
                'line_product_id': product_id,
                'line_product_default_code':line.get('physicalProperties' ,{}).get('sku', False) or False,
                'line_taxes': line_taxes
            }
            if store_variant_id:
                order_line_dict["line_variant_ids"] = store_variant_id
            order_lines.append((0, 0, order_line_dict))
        if float(data.get('priceSummary').get('shipping').get('amount')):
            order_lines += self._get_wix_shipping(channel_id,data.get('shippingInfo'))     
        if float(data.get('priceSummary').get('discount', {}).get('amount')):
            discount_line = self._get_wix_discount_lines(sdk,data,channel_id)
            discount_line.update({'line_taxes': tax_list})
            order_lines.append((0,0,discount_line))
        return order_lines

    def _get_wix_shipping(self, channel, shipping_line):
        name = 'wix_%s'%(shipping_line.get('title'))
        shipping_data={
                'line_name': name,
                'line_product_uom_qty': 1,
                'line_source': 'delivery',
        }
        if shipping_line.get('cost'):
            shipping_amount = float(shipping_line.get('cost').get('totalPriceAfterTax', {}).get('amount')) or float(shipping_line.get('cost').get('price').get('amount'))
            shipping_data.update({'line_price_unit': shipping_amount})
        return [(0,0,shipping_data)]

    def get_order_transaction(self, sdk, order_ids): # Getting Payment Method for orders
        """Developer Preview
            This API is subject to change. Bug fixes and new features will 
            be released based on developer feedback throughout the preview period.
            Doc ref: https://dev.wix.com/docs/rest/api-reference/wix-e-commerce/order-transactions/list-transactions-for-single-order
        args: 
            sdk: Api sdk obj to trigger wix api
            order_ids: It can be list of Ids or single string Id
        """
        def get_payment_method(orderTransactions):
            payment_method, data_dict = False, {}
            payments = orderTransactions.get('payments')
            if payments:
                if len(payments) > 1:
                    for payment in payments:
                        if payment.get('regularPaymentDetails',{}).get('status', '') == "APPROVED":
                            payment_method = payment.get('regularPaymentDetails', {}).get('paymentMethod')
                if not payment_method:
                    payment_method = payments[0].get('regularPaymentDetails').get('paymentMethod')
            if payment_method:
                data_dict = {orderTransactions.get('orderId'): payment_method}
            return data_dict
        order_paymentMethods_dict = {}
        try:
            order_ids = [order_ids] if not isinstance(order_ids, list) else order_ids
            data = sdk._post_data("https://www.wixapis.com/ecom/v1/payments/list-by-ids", params={'orderIds': order_ids}, auth=True)
            if data and data.get('data') and data.get('data').get('orderTransactions'):
                for orderTransactions in data.get('data').get('orderTransactions'):
                    order_paymentMethods_dict.update(get_payment_method(orderTransactions))
        except Exception as e:
            _logger.error(e, exc_info=True)
        return order_paymentMethods_dict

    def _process_order(self, sdk, channel, order):
        order_lines = self._get_wix_order_line(
            sdk, channel, order)
        method_title = False
        if order.get('shippingInfo'):
            method_title = order.get('shippingInfo').get('title')
        store_partner_id = order.get('buyerInfo')
        name = ''
        if order.get('buyerInfo'):
            if order.get('billingInfo').get('contactDetails').get('firstName'):
                name += order.get('billingInfo').get('contactDetails').get('firstName', '')
            if order.get('billingInfo').get('contactDetails').get('lastName'):
                name += " " if name else ""
                name += order.get('billingInfo').get('contactDetails').get('lastName', '')
        # -------------------Issue Fix Regarding Shippment And Invoice Date----------------------
        invoice_date = False
        shipping_date = False
        if order['activities']:
            for act in order["activities"]:
                if invoice_date and shipping_date:
                    break
                if act["type"] in ['INVOICE_ADDED','ORDER_PAID']:
                    invoice_date = act["createdDate"]
                if act["type"] in ['ORDER_FULFILLED','SHIPPING_CONFIRMATION_EMAIL_SENT']:
                    shipping_date = act["createdDate"]
        # ---------------------------------------------------------------------------------------
        order_dict = {
                    'name': order.get('number'),
                    'store_id': order.get('id'),
                    'channel_id': channel.id,
                    "channel": channel.channel,
                    'partner_id': store_partner_id.get('contactId') or store_partner_id.get('id') or order.get('billingInfo').get('email'),
                    'line_type': 'multi',
                    'carrier_id': method_title,
                    'line_ids': order_lines,
                    'currency': order['currency'],
                    'customer_name': name,
                    'customer_email': order.get('buyerInfo').get('email'),
                    'customer_phone': order.get('billingInfo', {}).get('contactDetails', {}).get('phone', False),
                    'customer_company': order.get('billingInfo', {}).get('contactDetails', {}).get('company', False),
                    # Wix States in odoo are comma seperated "payment_state,fullfillment_state"
                    'order_state': order['paymentStatus']+','+order['fulfillmentStatus'],
                    'date_order': order['createdDate'],
                    'confirmation_date': order['createdDate'],
                    # 'date_invoice': order.get('billingInfo', {}).get('paidDate') or False,
                    
                    # ---------------------------Fix Inovice And Shipping Date---------------------------
                    'date_invoice': invoice_date if invoice_date else order['createdDate'],
                    'date_shipping': shipping_date if shipping_date else order['createdDate'],
                    # -----------------------------------------------------------------------------------
                }
        if order.get('billingInfo'):
            order_dict.update({
                'invoice_partner_id': store_partner_id.get('contactId')  and f'billing_{store_partner_id.get("contactId")}' or f'billing_{store_partner_id.get("id")}' or order.get('billingInfo').get('email'),
            })
            if order.get('billingInfo').get('address'):
                order_dict.update({ 
                        'invoice_street': order.get('billingInfo').get('address').get('addressLine'),
                        # 'invoice_street2': order.get('billingInfo').get('address').get('addressLine2'),
                        'invoice_email': order.get('buyerInfo').get('email'),
                        'invoice_zip': order.get('billingInfo').get('address').get('postalCode'),
                        'invoice_phone': order.get('billingInfo').get('contactDetails').get('phone'),
                        'invoice_city': order.get('billingInfo').get('address').get('city'),
                        'invoice_state_code': order.get('billingInfo').get('address').get('subdivision'),
                        'invoice_state_name': order.get('billingInfo').get('address').get('subdivisionFullname'),
                        'invoice_country_code': order.get('billingInfo').get('address').get('country'),
                        })
                invoice_name = ''
                if order.get('billingInfo').get('contactDetails').get('firstName'):
                    invoice_name += order.get('billingInfo').get('contactDetails').get('firstName' ,'')
                if order.get('billingInfo').get('contactDetails').get('lastName'):
                    invoice_name += ' ' if invoice_name else ''
                    invoice_name += order.get('billingInfo').get('contactDetails').get('lastName')
                order_dict.update({ 'invoice_name': invoice_name})
        if order.get('shippingInfo', {}):
            shippingDestination = order.get('shippingInfo').get('logistics', {}).get('shippingDestination', {})
            if shippingDestination:
                try:
                    order_dict['same_shipping_billing'] = False
                    shipping_name = ''
                    if shippingDestination.get('contactDetails', {}).get('firstName', False):
                        shipping_name += shippingDestination.get('contactDetails', {}).get('firstName', '')
                    if shippingDestination.get('contactDetails', {}).get('lastName', False):
                        shipping_name += ' ' if shipping_name else ''
                        shipping_name += shippingDestination.get('contactDetails', {}).get('lastName', '')
                    order_dict.update({
                        'shipping_partner_id': store_partner_id.get('contactId') and f'shipping_{store_partner_id.get("contactId")}' or order.get('shippingInfo',{}).get('shipmentDetails',{}).get('address',{}).get('email'),
                        'shipping_name': shipping_name,
                    })
                    if shippingDestination:
                        order_dict.update({ 
                                'shipping_phone':shippingDestination.get('contactDetails',{}).get('phone'),
                                'shipping_street': shippingDestination.get('address',{}).get('addressLine'),
                                'shipping_street2': shippingDestination.get('address',{}).get('addressLine2'),
                                'shipping_email': order.get('buyerInfo',{}).get('email'),
                                'shipping_zip': shippingDestination.get('address',{}).get('postalCode'),
                                'shipping_city': shippingDestination.get('address',{}).get('city'),
                                'shipping_state_code': shippingDestination.get('address',{}).get('subdivision'),
                                'shipping_country_code': shippingDestination.get('address',{}).get('country'),
                                        })
                except Exception as e:
                    _logger.error('%r',e, exc_info=True)
                    order_dict['same_shipping_billing'] = True
        if self._context.get('order_with_payment_method') and order.get('paymentStatus') == 'PAID': 
            # add 'with_payment_method' context only when you are not following the complete flow 
            # of orders import if you are calling '_process_order' method from other custom method
            # (bacause method '_wix_import_orders' is already adding the payment method)
            payment_methods = self.get_order_transaction(sdk, order.get('id'))
            if payment_methods.get(order.get('id')):
                order_dict['payment_method'] = payment_methods.get(order.get('id'))
        return order_dict

    def wix_get_tax_line(self, channel_id, item):
        # Orders amount is calculating correctly in case of tax included
        if float(item.get('taxDetails').get('taxRate', 0)):
            tax_percent = float(item.get('taxDetails').get('taxRate', 0)) * 100
            include_in_price = True if channel_id.default_tax_type == 'include' else False
            if tax_percent > 0:
                tax_percent = round(tax_percent, 2)
                name = 'wix_incl_{}%'.format(tax_percent) if include_in_price else 'wix_excl_{}%'.format(tax_percent)
                return [{
                    'rate': tax_percent,
                    'name': name,
                    'include_in_price': include_in_price,
                    'tax_type': 'percent'
                }]
        return []

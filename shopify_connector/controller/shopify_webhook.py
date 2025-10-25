from odoo import http
from odoo.http import request, Response
from bs4 import BeautifulSoup
import requests
import json
import base64
import logging
_logger = logging.getLogger(__name__)

class ShopifyHookController(http.Controller):

    @http.route('/webhook/product', type='json', auth='public', cors='*', csrf=False, methods=['POST'])
    def get_shopify_product(self, **kwargs):
        shopify_connector = http.request.env['shopify.connector'].sudo().search([],limit=1)
        connection_status = shopify_connector.test_shopify_connection()
        if shopify_connector and connection_status == 'Connection success':
            single_product = json.loads(request.httprequest.data)
            _logger.info("This is get shopifywebhook product %s",single_product)
            products=[]
            products.append(single_product)
            #products_type = type(products)
            #_logger.info("Type of products: %s", products_type)
            sync_type = "sync_cron"
            shopify_product = http.request.env['shopify.product'].sudo()
            shopify_product.sync_product(products, shopify_connector, sync_type)
    
    @http.route('/webhook/customer', type='json', auth='public', cors='*', csrf=False, methods=['POST'])
    def get_shopify_customer(self, **kwargs):
        shopify_connector = http.request.env['shopify.connector'].sudo().search([],limit=1)
        connection_status = shopify_connector.test_shopify_connection()
        if shopify_connector and connection_status == 'Connection success':
            single_customer = json.loads(request.httprequest.data)
            _logger.info("This is get shopifywebhook customer %s",single_customer)
            customers=[]
            customers.append(single_customer)
            sync_type = "sync_cron"
            shopify_product = http.request.env['shopify.customer'].sudo()
            shopify_product.sync_customer(customers, shopify_connector, sync_type)
    
    @http.route('/webhook/order', type='json', auth='public', cors='*', csrf=False, methods=['POST'])
    def get_woodata_order(self, **kwargs):
        shopify_connector = http.request.env['shopify.connector'].sudo().search([],limit=1)
        connection_status = shopify_connector.test_shopify_connection()
        if shopify_connector and connection_status == 'Connection success':
            single_order = json.loads(request.httprequest.data)
            _logger.info("This is get shopifywebhook order %s",single_order)
            orders=[]
            orders.append(single_order)
            sync_type = "sync_cron"
            shopify_order = http.request.env['shopify.order'].sudo()
            shopify_order.sync_order(orders, shopify_connector.shopify_url, shopify_connector, sync_type)
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
        _logger.info("This is get shopifywebhook product")

        shopify_shop_domain = request.httprequest.headers.get('X-Shopify-Shop-Domain',False)
        if not shopify_shop_domain:
            _logger.info("Header X-Shopify-Shop-Domain not found")
            return {
                "status": "error",
                "message": "Header 'X-Shopify-Shop-Domain' not found"
            }
        
        shop_subdomain = shopify_shop_domain.split('.')[0]
        _logger.info("Shop Subdomain: %s", shop_subdomain)

        shopify_connector = http.request.env['shopify.connector'].sudo().search([('shopify_shop_name','=',shop_subdomain),('enable_product_webhook','=',True)],limit=1)
        connection_status = shopify_connector.test_shopify_connection()
        if shopify_connector and connection_status == 'Connection success':
            single_product = json.loads(request.httprequest.data)
            _logger.info("This is get shopifywebhook product %s",single_product)
            _logger.info("admin_graphql_api_id %s",single_product.get('admin_graphql_api_id'))
            shopify_connector.sudo().import_shopify_product_by_id(single_product.get('admin_graphql_api_id'))
    
    @http.route('/webhook/customer', type='json', auth='public', cors='*', csrf=False, methods=['POST'])
    def get_shopify_customer(self, **kwargs):
        response = json.loads(request.httprequest.data)
        _logger.info("This is get shopifywebhook customer %s",response)

        shopify_shop_domain = request.httprequest.headers.get('X-Shopify-Shop-Domain',False)
        if not shopify_shop_domain:
            _logger.info("Header X-Shopify-Shop-Domain not found")
            return {
                "status": "error",
                "message": "Header 'X-Shopify-Shop-Domain' not found"
            }
        
        shop_subdomain = shopify_shop_domain.split('.')[0]
        _logger.info("Shop Subdomain: %s", shop_subdomain)

        shopify_connector = http.request.env['shopify.connector'].sudo().search([('shopify_shop_name','=',shop_subdomain),('enable_customer_webhook','=',True)],limit=1)
        connection_status = shopify_connector.test_shopify_connection()
        if shopify_connector and connection_status == 'Connection success':
            _logger.info("admin_graphql_api_id %s",response.get('admin_graphql_api_id'))
            shopify_connector.sudo().import_shopify_customer_by_id(response.get('admin_graphql_api_id'))
    
    @http.route('/webhook/coupen', type='json', auth='public', cors='*', csrf=False, methods=['POST'])
    def get_shopify_coupen(self, **kwargs):
        response = json.loads(request.httprequest.data)
        _logger.info("This is get shopifywebhook coupen %s",response)
        shopify_shop_domain = request.httprequest.headers.get('X-Shopify-Shop-Domain',False)
        if not shopify_shop_domain:
            _logger.info("Header X-Shopify-Shop-Domain not found")
            return {
                "status": "error",
                "message": "Header 'X-Shopify-Shop-Domain' not found"
            }
        
        shop_subdomain = shopify_shop_domain.split('.')[0]
        _logger.info("Shop Subdomain: %s", shop_subdomain)

        shopify_connector = http.request.env['shopify.connector'].sudo().search([('shopify_shop_name','=',shop_subdomain),('enable_coupen_webhook','=',True)],limit=1)
        connection_status = shopify_connector.test_shopify_connection()
        if shopify_connector and connection_status == 'Connection success':
            _logger.info("admin_graphql_api_id %s",response.get('admin_graphql_api_id'))
            shopify_connector.sudo().import_shopify_coupon_by_id(response.get('admin_graphql_api_id'))
    
    @http.route('/webhook/order', type='json', auth='public', cors='*', csrf=False, methods=['POST'])
    def get_shopify_order(self, **kwargs):
        response = json.loads(request.httprequest.data)
        _logger.info("This is get shopifywebhook order %s",response)
        shopify_shop_domain = request.httprequest.headers.get('X-Shopify-Shop-Domain',False)
        if not shopify_shop_domain:
            _logger.info("Header X-Shopify-Shop-Domain not found")
            return {
                "status": "error",
                "message": "Header 'X-Shopify-Shop-Domain' not found"
            }
        
        shop_subdomain = shopify_shop_domain.split('.')[0]
        _logger.info("Shop Subdomain: %s", shop_subdomain)

        shopify_connector = http.request.env['shopify.connector'].sudo().search([('shopify_shop_name','=',shop_subdomain)],limit=1)
        connection_status = shopify_connector.test_shopify_connection()
        if shopify_connector and connection_status == 'Connection success':
            _logger.info("admin_graphql_api_id %s",response.get('admin_graphql_api_id'))
            shopify_connector.sudo().import_shopify_order_by_id(response.get('admin_graphql_api_id'))
        
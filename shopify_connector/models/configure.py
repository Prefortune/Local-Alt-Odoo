from odoo import api, fields, models, _
import requests
from odoo.exceptions import ValidationError,UserError
import json
import logging
_logger = logging.getLogger(__name__)
from odoo.http import request
from urllib.parse import urlparse, parse_qs

class ShopifyConnector(models.Model):
    _name = "shopify.connector"
    _description = "Shopify Connection"


    name = fields.Char(string="Store Name")
    shopify_shop_name = fields.Char(string="Shopify Store Name")
    shopify_api_key = fields.Char(string="Api key")
    shopify_access_token = fields.Char(string="Shopify Access Token")
    shopify_api_secret_key = fields.Char(string="Api Secret key")
    shopify_url = fields.Char(string="Shopify URL", compute="_compute_shopify_url", store=True)
    shopify_webhook_version = fields.Char(string="Shopify webhook version")
    shopify_connection_status = fields.Char(string='Shopify Connection Status')
    store_price_list = fields.Many2one('product.pricelist', string='Store PriceList', readonly=True)


    @api.depends('name', 'shopify_shop_name', 'shopify_api_key', 'shopify_access_token', 'shopify_webhook_version')
    def _compute_shopify_url(self):
        for record in self:
            record.shopify_url = "https://{api_key}:{api_access_token}@{shop_name}.myshopify.com/admin/api/{webhook_version}".format(
                api_key=record.shopify_api_key,
                api_access_token=record.shopify_access_token,
                shop_name=record.shopify_shop_name,
                webhook_version=record.shopify_webhook_version
            )

            if not record.store_price_list:
                pricelist_name = f"{record.name} Pricelist"
                find_pricelist = self.env['product.pricelist'].search([('name', '=', pricelist_name)])
                if find_pricelist:
                    pricelist = find_pricelist
                else:
                    pricelist = self.env['product.pricelist'].create({'name':pricelist_name})
                record.store_price_list = pricelist.id
            
            # create Product public Product access for images
            acl_pro_pro_name = "product.product shopify_connector Public Group"
            product_product_acl = self.env['ir.model.access'].search([('name', '=', acl_pro_pro_name)])
            if not product_product_acl:
                acl_model_id = self.env['ir.model'].search([('model', '=', 'product.product')])
                acl_user_group_id = self.env['res.groups'].search([('name', '=', 'Public')])
                create_product_product_acl = self.env['ir.model.access'].create({
                    'name': acl_pro_pro_name,
                    'model_id': acl_model_id.id,  
                    'group_id': acl_user_group_id.id,
                    'perm_read': 1
                })
                
            # create Product public Template access for images
            acl_pro_temp_name = "product.template shopify_connector Public Group"
            product_product_acl = self.env['ir.model.access'].search([('name', '=', acl_pro_temp_name)])
            if not product_product_acl:
                acl_model_id = self.env['ir.model'].search([('model', '=', 'product.template')])
                acl_user_group_id = self.env['res.groups'].search([('name', '=', 'Public')])
                create_product_template_acl = self.env['ir.model.access'].create({
                    'name': acl_pro_temp_name,
                    'model_id': acl_model_id.id,  
                    'group_id': acl_user_group_id.id,
                    'perm_read': 1
                })

    def test_shopify_connection(self):
        for record in self:
            try:
                # Sending a test request to Shopify API to check connection
                check_connection = "https://{api_key}:{api_access_token}@{shop_name}.myshopify.com/admin/oauth/access_scopes.json".format(
                    api_key=record.shopify_api_key,
                    api_access_token=record.shopify_access_token,
                    shop_name=record.shopify_shop_name
                )
                response = requests.get(check_connection)
                response.raise_for_status()
                record.shopify_connection_status = 'Connection success'
            
            except requests.exceptions.RequestException as e:
                record.shopify_connection_status = 'Connection Failed'
                raise UserError('Connection Failed Someting Wrong !!!')
        return record.shopify_connection_status

    def import_shopify_products(self):
        test_connection = self.test_shopify_connection()
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                main_url = shop_url + "/products.json?limit=250"
                shop_url = shop_url + "/products.json?limit=250"
                products = []
                next_page = True

                while next_page:
                    response = requests.get(shop_url)
                    response_data = response.json()
                    #_logger.info("response_data %s",response_data)
                    if 'products' in response_data:
                        products.extend(response_data['products'])
                        _logger.info(len(products))
                        _logger.info(response.headers)
                        next_page,shop_url = self.get_next_link(response.headers,main_url)
                    else:
                        next_page = False  # No 'Link' header means no pagination
                if products:
                    sync_type = "sync_button"
                    shopify_product = record.env['shopify.product']
                    shopify_product.sync_product(products, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Product Found in Shopify Store'))
                
    def import_shopify_customer(self):
        test_connection = self.test_shopify_connection()
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url

                main_url = shop_url + "/customers.json?limit=250"
                shop_url = shop_url + "/customers.json?limit=250"
                customers = []
                next_page = True

                while next_page:
                    response = requests.get(shop_url)
                    response_data = response.json()
                    #_logger.info("response_data %s",response_data)
                    if 'customers' in response_data:
                        customers.extend(response_data['customers'])
                        _logger.info(len(customers))
                        _logger.info(response.headers)
                        next_page,shop_url = self.get_next_link(response.headers,main_url)
                    else:
                        next_page = False  # No 'Link' header means no pagination
                if customers:
                    sync_type = "sync_button"
                    shopify_customer = record.env['shopify.customer']
                    shopify_customer.sync_customer(customers, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Customer Found in Shopify Store'))
     
    def import_shopify_order(self):
        test_connection = self.test_shopify_connection()
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                
                main_url = shop_url + "/orders.json?limit=250"
                shop_url = shop_url + "/orders.json?limit=250&status=any&ids=6154714120353"
                orders = []
                next_page = True

                while next_page:
                    response = requests.get(shop_url)
                    response_data = response.json()
                    #_logger.info("response_data %s",response_data)
                    if 'orders' in response_data:
                        orders.extend(response_data['orders'])
                        _logger.info(len(orders))
                        _logger.info(response.headers)
                        next_page,shop_url = self.get_next_link(response.headers,main_url)
                    else:
                        next_page = False  # No 'Link' header means no pagination
                if orders:
                    sync_type = "sync_button"
                    shopify_order = record.env['shopify.order']
                    shopify_order.sync_order(orders, shopify_connector.shopify_url, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Order Found in Shopify Store'))
                
    def import_shopify_coupon(self):
        test_connection = self.test_shopify_connection()
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                response = requests.get(shop_url + "/price_rules.json")
                _logger.info("response ------- %s",response)
                coupons = response.json()["price_rules"]
                _logger.info(json.dumps({"coupons":coupons}))
                if coupons:
                    sync_type = "sync_button"
                    shopify_coupon = record.env['shopify.coupon']
                    shopify_coupon.sync_coupon(coupons, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Order Found in Shopify Store'))
    
    def get_next_link(self,response_header,main_url):
        # Check if there is a next page
        if 'Link' in response_header:
            link_header = response_header['Link']
            _logger.info("link_header %s",link_header)
            # Search for the `rel="next"` part in the Link header
            links = link_header.split(',')
            # Find the part with rel="next"
            next_link = None
            for link in links:
                if 'rel="next"' in link:
                    next_link = link.strip().split(";")[0].strip('<>')
                _logger.info("rel_next ")
                # Extract the URL between the angle brackets <...>
            if next_link:
                parsed_url = urlparse(next_link)
                query_params = parse_qs(parsed_url.query)
                
                # Extract the value of page_info
                page_info = query_params.get('page_info', [None])[0]
                _logger.info("page_info %s",page_info)
                shop_url = main_url + '&page_info=' + page_info  # Update the URL for the next page
                _logger.info("shop_url %s ",shop_url)
                return True , shop_url
            else:
                next_page = False  # No more pages
                _logger.info("next_page 1 %s",next_page)
                return next_page , ''
        else:
            next_page = False  # No more pages
            _logger.info("next_page 2 %s",next_page)
            return next_page , ''

    # Cron Function
    def sync_product_cron(self):
        shopify_connectors = self.env['shopify.connector'].search([])
        for shopify_connector in shopify_connectors:
            _logger.info("Product Cron")
            shopify_connector.import_shopify_products()

    def sync_customer_cron(self):
        shopify_connectors = self.env['shopify.connector'].search([])
        for shopify_connector in shopify_connectors:
            _logger.info("Customer Cron")
            shopify_connector.import_shopify_customer()
    
    def sync_order_cron(self):
        shopify_connectors = self.env['shopify.connector'].search([])
        for shopify_connector in shopify_connectors:
            _logger.info("Orders Cron")
            shopify_connector.import_shopify_order()



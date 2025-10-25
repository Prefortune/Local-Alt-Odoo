from odoo import api, fields, models, _
import requests
from odoo.exceptions import ValidationError,UserError
import json
import logging
_logger = logging.getLogger(__name__)
from odoo.http import request

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
    currency_id = fields.Many2one('res.currency',string="Currency",default=lambda self: self.env.company.currency_id)
    store_price_list = fields.Many2one('product.pricelist', string='Store PriceList',compute="_compute_store_price_list", store=True)
    is_price_list_require = fields.Boolean(string="Is Pricelist Require For Price ?", default=False)

    force_accounting_date = fields.Boolean(string="Force Accounting Date", default=False)
    sale_journal = fields.Many2one('account.journal',string='Sale journal',domain=[('type','=','sale')])
    tag_ids = fields.Many2many('crm.tag', string='Sale order Tags')
    payment_journal = fields.Many2one('account.journal',string='Payment journal',domain=[('type','in',['bank','cash'])])
    
    product_create_webhook = fields.Char(string="Product create webhook")
    product_update_webhook = fields.Char(string="Product update webhook")
    customer_create_webhook = fields.Char(string="Customer create webhook")
    customer_update_webhook = fields.Char(string="Customer update webhook")
    order_create_webhook = fields.Char(string="Order create webhook")
    order_update_webhook = fields.Char(string="Order update webhook")
    coupen_create_webhook = fields.Char(string="Coupen create webhook")
    coupen_update_webhook = fields.Char(string="Coupen update webhook")

    enable_product_webhook = fields.Boolean(string="Enable Product Webhhok", default=True)
    enable_coupen_webhook = fields.Boolean(string="Enable Coupen Webhook", default=True)
    enable_customer_webhook = fields.Boolean(string="Enable Customer Webhook", default=True)

    @api.model
    def create(self,vals):
        result = super(ShopifyConnector, self).create(vals)
        self.cron_subscription()
        return result

    @api.depends('currency_id','name')
    def _compute_store_price_list(self):
        if self.name and self.currency_id:
            pricelist_name = f"{self.name} Pricelist"
            find_pricelist = self.env['product.pricelist'].search([('name', '=', pricelist_name),('currency_id', '=', self.currency_id.id)])
            if find_pricelist:
                pricelist = find_pricelist
            else:
                pricelist = self.env['product.pricelist'].create({'name':pricelist_name,'currency_id':self.currency_id.id})
            self.store_price_list = pricelist.id
    

    @api.depends('name', 'shopify_shop_name', 'shopify_api_key', 'shopify_access_token', 'shopify_webhook_version')
    def _compute_shopify_url(self):
        for record in self:
            record.shopify_url = "https://{shop_name}.myshopify.com/admin/api/{webhook_version}/graphql.json".format(
                shop_name=record.shopify_shop_name,
                webhook_version=record.shopify_webhook_version
            )

            # Set the headers with the access token
            headers = {
                "Content-Type": "application/graphql",
                "X-Shopify-Access-Token": record.shopify_access_token
            }
               
            # if not record.store_price_list:
            #     pricelist_name = f"{record.name} Pricelist"
            #     find_pricelist = self.env['product.pricelist'].search([('name', '=', pricelist_name),('currency_id', '=', record.currency_id.id)])
            #     if find_pricelist:
            #         pricelist = find_pricelist
            #     else:
            #         pricelist = self.env['product.pricelist'].create({'name':pricelist_name,'currency_id':record.currency_id.id})
            #     record.store_price_list = pricelist.id
            
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
        return record.shopify_connection_status

    def import_shopify_products(self):
        test_connection = self.test_shopify_connection()
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                
                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": record.shopify_access_token
                }
                
                # Dynamic number of products to fetch
                first_products = 10  # This can be dynamically set as needed
                has_next_page = True
                cursor = None  # Initially no cursor
                all_products = []  # List to store all products

                while has_next_page:
                    # GraphQL query with dynamic variable for `first` and `after` (cursor)
                    query = """
                        query ($first: Int!, $after: String) {
                            products(first: $first, after: $after, sortKey: ID) {
                                nodes {
                                    id
                                    title
                                    descriptionHtml
                                    totalInventory
                                    totalVariants
                                    productCategory {
                                        productTaxonomyNode {
                                            fullName
                                            id
                                        }
                                    }
                                    options {
                                        id
                                        name
                                        values
                                    }
                                    priceRangeV2 {
                                        maxVariantPrice {
                                            amount
                                        }
                                        minVariantPrice {
                                            amount
                                        }
                                    }
                                    featuredMedia {
                                        preview {
                                            image {
                                                id
                                                src
                                            }
                                        }
                                    }
                                    variants(first: 100, sortKey: ID) {
                                        nodes {
                                            id
                                            displayName
                                            sku
                                            price
                                            title
                                            inventoryQuantity
                                            image {
                                                id
                                                src
                                                url
                                            }
                                        }
                                    }
                                    status
                                }
                                pageInfo {
                                    hasNextPage
                                    hasPreviousPage
                                    startCursor
                                    endCursor
                                }
                            }
                        }
                    """
                    
                    # Variables to pass into the query (e.g., how many products to fetch)
                    variables = {
                        "first": first_products,
                        "after": cursor  # Pass the cursor for pagination
                    }

                    # Make the POST request to Shopify GraphQL API
                    response = requests.post(shop_url, json={'query': query, 'variables': variables}, headers=headers)
                    
                    # Log the response
                    if response.status_code == 200:
                        products_data = response.json()
                        # _logger.info("Data: %s", json.dumps(products_data))
                        
                        # Process products here (products_data['products_data']['products']['nodes'])
                        products = products_data['data']['products']['nodes']
                        # _logger.info("products: %s", json.dumps(products))
                        all_products.extend(products)
                        # Example: Add products to the system, or do further processing
                        
                        # Check for pagination
                        page_info = products_data['data']['products']['pageInfo']
                        has_next_page = page_info['hasNextPage']
                        
                        # Set the cursor for the next page
                        if has_next_page:
                            cursor = page_info['endCursor']
                        else:
                            cursor = None  # No more pages
                    else:
                        _logger.error("Error fetching data: %s", response.text)
                        raise ValidationError(_('Error fetching data'))
                        break  # Exit the loop if an error occurs
                _logger.info(" all products: %s", json.dumps(all_products))

                if all_products:
                    sync_type = "sync_button"
                    shopify_product = record.env['shopify.product']
                    shopify_product.sync_product(all_products, shopify_connector, sync_type)
                    # else:
                    #     raise ValidationError(_('No Product Found in Shopify Store'))
                
    def import_shopify_customer(self):
        test_connection = self.test_shopify_connection()
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                
                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": record.shopify_access_token
                }
                
                # Dynamic number of products to fetch
                first_customer = 5  # This can be dynamically set as needed
                has_next_page = True
                cursor = None  # Initially no cursor
                all_customers = []  # List to store all products

                while has_next_page:
                    # GraphQL query with dynamic variable for `first` and `after` (cursor)
                    query = """
                        query ($first: Int!, $after: String) {
                            customers(first: $first, after: $after, sortKey: ID) {
                                nodes {
                                    id
                                    email
                                    firstName
                                    lastName
                                    defaultAddress {
                                        id
                                        name
                                        address1
                                        address2
                                        city
                                        zip
                                        phone
                                        province
                                        provinceCode
                                        country
                                        countryCode
                                        company
                                    }
                                    displayName
                                    phone
                                }
                                pageInfo {
                                    hasNextPage
                                    startCursor
                                    hasPreviousPage
                                    endCursor
                                    }
                                }
                            }
                    """
                    
                    # Variables to pass into the query (e.g., how many products to fetch)
                    variables = {
                        "first": first_customer,
                        "after": cursor  # Pass the cursor for pagination
                    }

                    # Make the POST request to Shopify GraphQL API
                    response = requests.post(shop_url, json={'query': query, 'variables': variables}, headers=headers)
                    
                    # Log the response
                    if response.status_code == 200:
                        customers_data = response.json()
                        # _logger.info("Data: %s", json.dumps(customers_data))
                        
                        # Process products here (customers_data['customers_data']['products']['nodes'])
                        customers = customers_data['data']['customers']['nodes']
                        # _logger.info("products: %s", json.dumps(products))
                        all_customers.extend(customers)
                        # Example: Add products to the system, or do further processing
                        
                        # Check for pagination
                        page_info = customers_data['data']['customers']['pageInfo']
                        has_next_page = page_info['hasNextPage']
                        
                        # Set the cursor for the next page
                        if has_next_page:
                            cursor = page_info['endCursor']
                        else:
                            cursor = None  # No more pages
                    else:
                        _logger.error("Error fetching data: %s", response.text)
                        raise ValidationError(_('Error fetching data'))
                        break  # Exit the loop if an error occurs
                    _logger.info("CUSTOMER %s", all_customers)
                # _logger.info(" all Customer: %s", json.dumps(all_customers))

            # if shopify_connector and connection_status == 'Connection success':
            #     shop_url = shopify_connector.shopify_url
            #     response = requests.get(shop_url + "/customers.json")
            #     customers = response.json()["customers"]
            #     _logger.info(response.json())
                if all_customers:
                    sync_type = "sync_button"
                    shopify_customer = record.env['shopify.customer']
                    shopify_customer.sync_customer(all_customers, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Customer Found in Shopify Store'))
    
    def import_shopify_order(self):
        test_connection = self.test_shopify_connection()
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": record.shopify_access_token
                }
                
                # Dynamic number of products to fetch
                first_order = 10  # This can be dynamically set as needed
                has_next_page = True
                cursor = None  # Initially no cursor
                all_orders = []  # List to store all products

                while has_next_page:
                    # GraphQL query with dynamic variable for `first` and `after` (cursor)
                    query = """
                        query ($first: Int!, $after: String) {
                            orders(first: $first, after: $after, sortKey: ID) {
                                nodes {
                                    id
                                    confirmationNumber
                                    taxesIncluded
                                    customer {
                                        id
                                        email
                                        displayName
                                    }
                                    billingAddressMatchesShippingAddress
                                    billingAddress {
                                        address1
                                        address2
                                        city
                                        company
                                        country
                                        countryCode
                                        id
                                        name
                                        phone
                                        province
                                        provinceCode
                                        zip
                                    }
                                    shippingAddress {
                                        address1
                                        address2
                                        city
                                        company
                                        country
                                        countryCode
                                        id
                                        name
                                        phone
                                        province
                                        provinceCode
                                        zip
                                    }
                                    lineItems(first: 250) {
                                        nodes {
                                            id
                                            currentQuantity
                                            discountedTotal
                                            discountedUnitPrice
                                            originalTotal
                                            originalUnitPrice
                                            sku
                                            quantity
                                            totalDiscount
                                            variant {
                                                id
                                                price
                                                sku
                                                title
                                                product {
                                                    status
                                                    id
                                                }
                                            }
                                            taxLines(first: 2) {
                                                price
                                                rate
                                                ratePercentage
                                                title
                                            }
                                        }
                                    }
                                    name
                                    subtotalPrice
                                    totalReceived
                                    totalRefunded
                                    totalTax
                                    totalDiscounts
                                    discountCode
                                    discountCodes
                                    discountApplications(first: 250) {
                                        nodes {
                                            allocationMethod
                                            index
                                            targetSelection
                                            targetType
                                            ... on AutomaticDiscountApplication {
                                                __typename
                                                index
                                                title
                                                targetType
                                                allocationMethod
                                            }
                                            ... on DiscountCodeApplication {
                                                __typename
                                                allocationMethod
                                                code
                                                index
                                                targetSelection
                                                targetType
                                            }
                                            ... on ManualDiscountApplication {
                                                description
                                                allocationMethod
                                                index
                                                targetSelection
                                                targetType
                                                title
                                            }
                                            ... on ScriptDiscountApplication {
                                                __typename
                                                allocationMethod
                                                description
                                                index
                                                targetSelection
                                                targetType
                                                title
                                            }
                                        }
                                    }
                                    displayFinancialStatus
                                    displayFulfillmentStatus
                                }
                                pageInfo {
                                    hasNextPage
                                    startCursor
                                    hasPreviousPage
                                    endCursor
                                    }
                                }
                            }
                        """
                    
                    # Variables to pass into the query (e.g., how many products to fetch)
                    variables = {
                        "first": first_order,
                        "after": cursor  # Pass the cursor for pagination
                    }

                    # Make the POST request to Shopify GraphQL API
                    response = requests.post(shop_url, json={'query': query, 'variables': variables}, headers=headers)
                    
                    # Log the response
                    if response.status_code == 200:
                        orders_data = response.json()
                        # _logger.info("Data: %s", json.dumps(customers_data))
                        
                        # Process products here (customers_data['customers_data']['products']['nodes'])
                        orders = orders_data['data']['orders']['nodes']
                        # _logger.info("products: %s", json.dumps(products))
                        all_orders.extend(orders)
                        # Example: Add products to the system, or do further processing
                        
                        # Check for pagination
                        page_info = orders_data['data']['orders']['pageInfo']
                        has_next_page = page_info['hasNextPage']
                        
                        # Set the cursor for the next page
                        if has_next_page:
                            cursor = page_info['endCursor']
                        else:
                            cursor = None  # No more pages
                    else:
                        _logger.error("Error fetching data: %s", response.text)
                        raise ValidationError(_('Error fetching data'))
                        break  # Exit the loop if an error occurs
                _logger.info("Orders %s", all_orders)
                # response = requests.get(shop_url + "/orders.json?status=any")
                # orders = response.json()["orders"]
                # _logger.info(json.dumps({"orders":orders}))
                if all_orders:
                    # cust_sync = self.import_shopify_customer()
                    # _logger.info("order in")
                    sync_type = "sync_button"
                    shopify_order = record.env['shopify.order']
                    shopify_order.sync_order(all_orders, shop_url, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Order Found in Shopify Store'))
                
    def import_shopify_coupon(self):
        test_connection = self.test_shopify_connection()
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": record.shopify_access_token
                }
                
                # Dynamic number of products to fetch
                first_discount = 5  # This can be dynamically set as needed
                has_next_page = True
                cursor = None  # Initially no cursor
                all_codediscountnodes = []  # List to store all products

                while has_next_page:
                    # GraphQL query with dynamic variable for `first` and `after` (cursor)
                    query = """
                        query ($first: Int!, $after: String) {
                            codeDiscountNodes(first: $first, after: $after, sortKey: ID) {
                               nodes {
                                    id
                                    codeDiscount {
                                        ... on DiscountCodeBxgy {
                                        title
                                        summary
                                        discountClass
                                        endsAt
                                        startsAt
                                        status
                                        customerBuys {
                                            value {
                                            ... on DiscountPurchaseAmount {
                                                __typename
                                                amount
                                            }
                                            ... on DiscountQuantity {
                                                __typename
                                                quantity
                                            }
                                            }
                                            items {
                                            ... on DiscountProducts {
                                                __typename
                                                productVariants(first: 250) {
                                                nodes {
                                                    id
                                                }
                                                }
                                                products(first: 250) {
                                                nodes {
                                                    id
                                                }
                                                }
                                            }
                                            ... on AllDiscountItems {
                                                __typename
                                                allItems
                                            }
                                            }
                                        }
                                        customerGets {
                                            value {
                                            ... on DiscountAmount {
                                                __typename
                                                amount {
                                                amount
                                                currencyCode
                                                }
                                                appliesOnEachItem
                                            }
                                            ... on DiscountOnQuantity {
                                                __typename
                                                quantity {
                                                quantity
                                                }
                                            }
                                            ... on DiscountPercentage {
                                                __typename
                                                percentage
                                            }
                                            }
                                            items {
                                            ... on DiscountProducts {
                                                __typename
                                                productVariants(first: 250) {
                                                nodes {
                                                    id
                                                }
                                                }
                                                products(first: 250) {
                                                nodes {
                                                    id
                                                }
                                                }
                                            }
                                            ... on AllDiscountItems {
                                                __typename
                                                allItems
                                            }
                                            }
                                        }
                                        customerSelection {
                                            ... on DiscountCustomerAll {
                                            __typename
                                            allCustomers
                                            }
                                            ... on DiscountCustomers {
                                            __typename
                                            customers {
                                                id
                                            }
                                            }
                                        }
                                        appliesOncePerCustomer
                                        }
                                        ... on DiscountCodeBasic {
                                        title
                                        summary
                                        discountClass
                                        endsAt
                                        startsAt
                                        status
                                        customerGets {
                                            items {
                                            ... on DiscountProducts {
                                                __typename
                                                productVariants(first: 250) {
                                                nodes {
                                                    id
                                                }
                                                }
                                                products(first: 250) {
                                                nodes {
                                                    id
                                                }
                                                }
                                            }
                                            ... on AllDiscountItems {
                                                __typename
                                                allItems
                                            }
                                            }
                                            value {
                                            ... on DiscountAmount {
                                                __typename
                                                amount {
                                                amount
                                                currencyCode
                                                }
                                                appliesOnEachItem
                                            }
                                            ... on DiscountOnQuantity {
                                                __typename
                                                effect {
                                                ... on DiscountAmount {
                                                    __typename
                                                    amount {
                                                    amount
                                                    currencyCode
                                                    }
                                                    appliesOnEachItem
                                                }
                                                ... on DiscountPercentage {
                                                    __typename
                                                    percentage
                                                }
                                                }
                                                quantity {
                                                quantity
                                                }
                                            }
                                            ... on DiscountPercentage {
                                                __typename
                                                percentage
                                            }
                                            }
                                        }
                                        customerSelection {
                                            ... on DiscountCustomerAll {
                                            __typename
                                            allCustomers
                                            }
                                            ... on DiscountCustomers {
                                            __typename
                                            customers {
                                                id
                                            }
                                            }
                                        }
                                        appliesOncePerCustomer
                                        minimumRequirement {
                                            ... on DiscountMinimumQuantity {
                                            __typename
                                            greaterThanOrEqualToQuantity
                                            }
                                            ... on DiscountMinimumSubtotal {
                                            __typename
                                            greaterThanOrEqualToSubtotal {
                                                amount
                                            }
                                            }
                                        }
                                        shareableUrls {
                                            targetType
                                            title
                                            url
                                        }
                                        }
                                        ... on DiscountCodeFreeShipping {
                                        title
                                        summary
                                        discountClass
                                        endsAt
                                        startsAt
                                        status
                                        customerSelection {
                                            ... on DiscountCustomerAll {
                                            __typename
                                            allCustomers
                                            }
                                            ... on DiscountCustomers {
                                            __typename
                                            customers {
                                                id
                                            }
                                            }
                                        }
                                        appliesOncePerCustomer
                                        }
                                    }
                                    }
                                pageInfo {
                                    hasNextPage
                                    startCursor
                                    hasPreviousPage
                                    endCursor
                                    }
                                }
                            }
                    """
                    
                    # Variables to pass into the query (e.g., how many products to fetch)
                    variables = {
                        "first": first_discount,
                        "after": cursor  # Pass the cursor for pagination
                    }

                    # Make the POST request to Shopify GraphQL API
                    response = requests.post(shop_url, json={'query': query, 'variables': variables}, headers=headers)
                    
                    # Log the response
                    if response.status_code == 200:
                        discountnodes_data = response.json()
                        # _logger.info("Data: %s", json.dumps(customers_data))
                        
                        # Process products here (customers_data['customers_data']['products']['nodes'])
                        codediscountnodes = discountnodes_data['data']['codeDiscountNodes']['nodes']
                        # _logger.info("products: %s", json.dumps(products))
                        all_codediscountnodes.extend(codediscountnodes)
                        # Example: Add products to the system, or do further processing
                        
                        # Check for pagination
                        page_info = discountnodes_data['data']['codeDiscountNodes']['pageInfo']
                        has_next_page = page_info['hasNextPage']
                        
                        # Set the cursor for the next page
                        if has_next_page:
                            cursor = page_info['endCursor']
                        else:
                            cursor = None  # No more pages
                    else:
                        _logger.error("Error fetching data: %s", response.text)
                        raise ValidationError(_('Error fetching data'))
                        break  # Exit the loop if an error occurs
                _logger.info("Discount Node %s", all_codediscountnodes)
                
                # response = requests.get(shop_url + "/price_rules.json")
                # coupons = response.json()["price_rules"]
                # _logger.info(json.dumps({"coupons":coupons}))
                if all_codediscountnodes:
                    sync_type = "sync_button"
                    shopify_coupon = record.env['shopify.coupon']
                    shopify_coupon.sync_coupon(all_codediscountnodes, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Order Found in Shopify Store'))
    
    def import_shopify_coupon_by_id(self,coupen_id):
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": record.shopify_access_token
                }
                
                # Dynamic number of products to fetch
                all_codediscountnodes = []  # List to store all products

                query = """
                    query ($id: ID!) {
                        codeDiscountNode(id: $id) {
                                id
                                codeDiscount {
                                    ... on DiscountCodeBxgy {
                                    title
                                    summary
                                    discountClass
                                    endsAt
                                    startsAt
                                    status
                                    customerBuys {
                                        value {
                                        ... on DiscountPurchaseAmount {
                                            __typename
                                            amount
                                        }
                                        ... on DiscountQuantity {
                                            __typename
                                            quantity
                                        }
                                        }
                                        items {
                                        ... on DiscountProducts {
                                            __typename
                                            productVariants(first: 250) {
                                            nodes {
                                                id
                                            }
                                            }
                                            products(first: 250) {
                                            nodes {
                                                id
                                            }
                                            }
                                        }
                                        ... on AllDiscountItems {
                                            __typename
                                            allItems
                                        }
                                        }
                                    }
                                    customerGets {
                                        value {
                                        ... on DiscountAmount {
                                            __typename
                                            amount {
                                            amount
                                            currencyCode
                                            }
                                            appliesOnEachItem
                                        }
                                        ... on DiscountOnQuantity {
                                            __typename
                                            quantity {
                                            quantity
                                            }
                                        }
                                        ... on DiscountPercentage {
                                            __typename
                                            percentage
                                        }
                                        }
                                        items {
                                        ... on DiscountProducts {
                                            __typename
                                            productVariants(first: 250) {
                                            nodes {
                                                id
                                            }
                                            }
                                            products(first: 250) {
                                            nodes {
                                                id
                                            }
                                            }
                                        }
                                        ... on AllDiscountItems {
                                            __typename
                                            allItems
                                        }
                                        }
                                    }
                                    customerSelection {
                                        ... on DiscountCustomerAll {
                                        __typename
                                        allCustomers
                                        }
                                        ... on DiscountCustomers {
                                        __typename
                                        customers {
                                            id
                                        }
                                        }
                                    }
                                    appliesOncePerCustomer
                                    }
                                    ... on DiscountCodeBasic {
                                    title
                                    summary
                                    discountClass
                                    endsAt
                                    startsAt
                                    status
                                    customerGets {
                                        items {
                                        ... on DiscountProducts {
                                            __typename
                                            productVariants(first: 250) {
                                            nodes {
                                                id
                                            }
                                            }
                                            products(first: 250) {
                                            nodes {
                                                id
                                            }
                                            }
                                        }
                                        ... on AllDiscountItems {
                                            __typename
                                            allItems
                                        }
                                        }
                                        value {
                                        ... on DiscountAmount {
                                            __typename
                                            amount {
                                            amount
                                            currencyCode
                                            }
                                            appliesOnEachItem
                                        }
                                        ... on DiscountOnQuantity {
                                            __typename
                                            effect {
                                            ... on DiscountAmount {
                                                __typename
                                                amount {
                                                amount
                                                currencyCode
                                                }
                                                appliesOnEachItem
                                            }
                                            ... on DiscountPercentage {
                                                __typename
                                                percentage
                                            }
                                            }
                                            quantity {
                                            quantity
                                            }
                                        }
                                        ... on DiscountPercentage {
                                            __typename
                                            percentage
                                        }
                                        }
                                    }
                                    customerSelection {
                                        ... on DiscountCustomerAll {
                                        __typename
                                        allCustomers
                                        }
                                        ... on DiscountCustomers {
                                        __typename
                                        customers {
                                            id
                                        }
                                        }
                                    }
                                    appliesOncePerCustomer
                                    minimumRequirement {
                                        ... on DiscountMinimumQuantity {
                                        __typename
                                        greaterThanOrEqualToQuantity
                                        }
                                        ... on DiscountMinimumSubtotal {
                                        __typename
                                        greaterThanOrEqualToSubtotal {
                                            amount
                                        }
                                        }
                                    }
                                    shareableUrls {
                                        targetType
                                        title
                                        url
                                    }
                                    }
                                    ... on DiscountCodeFreeShipping {
                                    title
                                    summary
                                    discountClass
                                    endsAt
                                    startsAt
                                    status
                                    customerSelection {
                                        ... on DiscountCustomerAll {
                                        __typename
                                        allCustomers
                                        }
                                        ... on DiscountCustomers {
                                        __typename
                                        customers {
                                            id
                                        }
                                        }
                                    }
                                    appliesOncePerCustomer
                                    }
                                }
                            }
                        }
                """
                
                # Variables to pass into the query (e.g., how many products to fetch)
                variables = {
                    "id": coupen_id,
                }

                # Make the POST request to Shopify GraphQL API
                response = requests.post(shop_url, json={'query': query, 'variables': variables}, headers=headers)
                
                # Log the response
                if response.status_code == 200:
                    discountnodes_data = response.json()
                    #_logger.info("Data: %s", json.dumps(response))
                    
                    all_codediscountnodes.insert(0,discountnodes_data.get("data", {}).get('codeDiscountNode',{}))                       
                else:
                    _logger.error("Error fetching data: %s", response.text)
                    raise ValidationError(_('Error fetching data'))
                _logger.info("Discount Node %s", all_codediscountnodes)
                
                # response = requests.get(shop_url + "/price_rules.json")
                # coupons = response.json()["price_rules"]
                # _logger.info(json.dumps({"coupons":coupons}))
                if all_codediscountnodes:
                    sync_type = "sync_button"
                    shopify_coupon = record.env['shopify.coupon']
                    shopify_coupon.sync_coupon(all_codediscountnodes, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Order Found in Shopify Store'))
    
    def import_shopify_customer_by_id(self, customer_id):
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                
                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": record.shopify_access_token
                }
                
                # Dynamic number of products to fetch
                all_customers = []  # List to store all products

                # GraphQL query with dynamic variable for `first` and `after` (cursor)
                query = """
                    query ($id: ID!) {
                        customer(id: $id) {
                            id
                            email
                            firstName
                            lastName
                            displayName
                            phone
                            defaultAddress {
                                id
                                address1
                                address2
                                city
                                firstName
                                name
                                zip
                                phone
                                province
                                provinceCode
                                country
                                countryCode
                                company
                            }
                        }
                    }
                """
                    
                # Variables to pass into the query (e.g., how many products to fetch)
                variables = {
                    "id": customer_id,
                }

                # Make the POST request to Shopify GraphQL API
                response = requests.post(shop_url, json={'query': query, 'variables': variables}, headers=headers)
                
                # Log the response
                if response.status_code == 200:
                    customers_data = response.json()
                    _logger.info("Data: %s", json.dumps(customers_data))
                    
                    # Process products here (customers_data['customers_data']['products']['nodes'])
                    all_customers.insert(0,customers_data.get("data", {}).get("customer", {}))
                    # _logger.info("products: %s", json.dumps(products))
                else:
                    _logger.error("Error fetching data: %s", response.text)
                    raise ValidationError(_('Error fetching data'))
                    break  # Exit the loop if an error occurs
                _logger.info("CUSTOMER_BY_ID %s", all_customers)
                if all_customers and all_customers != [{}]:
                    sync_type = "sync_button"
                    shopify_customer = record.env['shopify.customer']
                    shopify_customer.sync_customer(all_customers, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Customer Found in Shopify Store'))
    
    #def import_shopify_product_by_id(self,product_id):
    def import_shopify_product_by_id(self,product_id):
        #product_id = "gid://shopify/Product/8070838386849"
        for record in self:
            _logger.info("import_shopify_product_by_id record")
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                
                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": record.shopify_access_token
                }
                
                all_products = []  # List to store all products

                # GraphQL query with dynamic variable for `first` and `after` (cursor)
                query = """
                    query ($id: ID!) {
                        product(id: $id) {
                                id
                                title
                                descriptionHtml
                                totalInventory
                                totalVariants
                                status
                                productCategory {
                                    productTaxonomyNode {
                                        fullName
                                        id
                                    }
                                }
                                options {
                                    id
                                    name
                                    values
                                }
                                priceRangeV2 {
                                    maxVariantPrice {
                                        amount
                                    }
                                    minVariantPrice {
                                        amount
                                    }
                                }
                                featuredMedia {
                                    preview {
                                        image {
                                            id
                                            src
                                        }
                                    }
                                }
                                variants(first: 250, sortKey: ID) {
                                    nodes {
                                        id
                                        displayName
                                        price
                                        title
                                        sku
                                        inventoryQuantity
                                        image {
                                            id
                                            src
                                            url
                                        }
                                    }
                                }
                                status
                        
                        }
                    }
                """
                
                # Variables to pass into the query (e.g., how many products to fetch)
                variables = {
                    "id": product_id,
                }

                # Make the POST request to Shopify GraphQL API
                response = requests.post(shop_url, json={'query': query, 'variables': variables}, headers=headers)
                
                # Log the response
                if response.status_code == 200:
                    products_data = response.json()
                    _logger.info("Data: %s", json.dumps(products_data))
                    
                    # _logger.info("products: %s", json.dumps(products))
                    all_products.insert(0,products_data.get("data", {}).get("product", {}))
                    # Example: Add products to the system, or do further processing
                    
                else:
                    _logger.error("Error fetching data: %s", response.text)
                    raise ValidationError(_('Error fetching data'))
                    break  # Exit the loop if an error occurs
                _logger.info(" all products: %s", json.dumps(all_products))

                if all_products and all_products != [{}]:
                    sync_type = "sync_button"
                    shopify_product = record.env['shopify.product']
                    shopify_product.sync_product(all_products, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Product Found in Shopify Store'))
    
    #def import_shopify_order_by_id(self,order_id):
    def import_shopify_order_by_id(self,order_id):
        #order_id = "gid://shopify/Order/6154652385441"
        for record in self:
            shopify_connector = record.env['shopify.connector'].search([('id', '=', record.id)])
            connection_status = record.test_shopify_connection()
            if shopify_connector and connection_status == 'Connection success':
                shop_url = shopify_connector.shopify_url
                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": record.shopify_access_token
                }
                
                all_orders = []  # List to store all products

                query = """
                    query ($id: ID!) {
                        order(id: $id) {
                            id
                            createdAt
                            confirmationNumber
                            taxesIncluded
                            customer {
                                id
                                email
                                displayName
                            }
                            billingAddressMatchesShippingAddress
                            billingAddress {
                                address1
                                address2
                                city
                                company
                                country
                                countryCode
                                id
                                name
                                phone
                                province
                                provinceCode
                                zip
                            }
                            shippingAddress {
                                address1
                                address2
                                city
                                company
                                country
                                countryCode
                                id
                                name
                                phone
                                province
                                provinceCode
                                zip
                            }
                            lineItems(first: 250) {
                                nodes {
                                    id
                                    name
                                    currentQuantity
                                    discountedTotal
                                    discountedUnitPrice
                                    originalTotal
                                    originalUnitPrice
                                    sku
                                    quantity
                                    totalDiscount
                                    variant {
                                        id
                                        price
                                        sku
                                        title
                                        product {
                                            status
                                            id
                                        }
                                    }
                                    taxLines(first: 2) {
                                        price
                                        rate
                                        ratePercentage
                                        title
                                    }
                                }
                            }
                            fulfillments {
                                displayStatus
                            }
                            name
                            subtotalPrice
                            totalReceived
                            totalRefunded
                            totalTax
                            totalDiscounts
                            discountCode
                            discountCodes
                            discountApplications(first: 250) {
                                nodes {
                                    allocationMethod
                                    index
                                    targetSelection
                                    targetType
                                    ... on AutomaticDiscountApplication {
                                        __typename
                                        index
                                        title
                                        targetType
                                        allocationMethod
                                    }
                                    ... on DiscountCodeApplication {
                                        __typename
                                        allocationMethod
                                        code
                                        index
                                        targetSelection
                                        targetType
                                    }
                                    ... on ManualDiscountApplication {
                                        description
                                        allocationMethod
                                        index
                                        targetSelection
                                        targetType
                                        title
                                    }
                                    ... on ScriptDiscountApplication {
                                        __typename
                                        allocationMethod
                                        description
                                        index
                                        targetSelection
                                        targetType
                                        title
                                    }
                                }
                            }
                            displayFinancialStatus
                            displayFulfillmentStatus
                        }
                        }
                    """
                
                # Variables to pass into the query (e.g., how many products to fetch)
                variables = {
                    "id": order_id,
                }

                # Make the POST request to Shopify GraphQL API
                response = requests.post(shop_url, json={'query': query, 'variables': variables}, headers=headers)
                
                # Log the response
                if response.status_code == 200:
                    orders_data = response.json()
                    _logger.info("Data: %s", json.dumps(orders_data))
                    
                    # _logger.info("products: %s", json.dumps(products))
                    all_orders.insert(0,orders_data.get("data", {}).get("order", {}))
                    # all_orders Add products to the system, or do further processing
                else:
                    _logger.error("Error fetching data: %s", response.text)
                    raise ValidationError(_('Error fetching data'))
                    break  # Exit the loop if an error occurs
                _logger.info("Orders %s", all_orders)
                # response = requests.get(shop_url + "/orders.json?status=any")
                # orders = response.json()["orders"]
                # _logger.info(json.dumps({"orders":orders}))
                if all_orders and all_orders != [{}]:
                    # cust_sync = self.import_shopify_customer()
                    # _logger.info("order in")
                    sync_type = "sync_button"
                    shopify_order = record.env['shopify.order']
                    shopify_order.sync_order(all_orders, shop_url, shopify_connector, sync_type)
                else:
                    raise ValidationError(_('No Order Found in Shopify Store'))
    

    def cron_subscription(self):
        for record in self:
            shop_url = record.shopify_url
            callback_url = record.get_base_url()
            #callback_url = 'https://41b1-150-129-151-163.ngrok-free.app'
            helper = self.env['helper.utils']

            # Set the headers with the access token
            headers = {
                "Content-Type": "application/json",  # Correct header
                "X-Shopify-Access-Token": record.shopify_access_token
            }

            mutation = helper.get_graphql_query('webhook')
            
            # Input for the mutation
            webhooks_input = [
                {
                    "topic": "PRODUCTS_CREATE",  # Event for product updates
                    "webhookSubscription": {
                        "callbackUrl": callback_url+'/webhook/product',
                        "format": "JSON"  # You can also use "XML" if needed
                    }
                },
                {
                    "topic": "PRODUCTS_UPDATE",  # Event for product updates
                    "webhookSubscription": {
                        "callbackUrl": callback_url+'/webhook/product',
                        "format": "JSON"  # You can also use "XML" if needed
                    }
                },
                {
                    "topic": "CUSTOMERS_CREATE",  # Event for product updates
                    "webhookSubscription": {
                        "callbackUrl": callback_url+'/webhook/customer',
                        "format": "JSON"  # You can also use "XML" if needed
                    }
                },
                {
                    "topic": "CUSTOMERS_UPDATE",  # Event for product updates
                    "webhookSubscription": {
                        "callbackUrl": callback_url+'/webhook/customer',
                        "format": "JSON"  # You can also use "XML" if needed
                    }
                },
                {
                    "topic": "DISCOUNTS_CREATE",  # Event for product updates
                    "webhookSubscription": {
                        "callbackUrl": callback_url+'/webhook/coupen',
                        "format": "JSON"  # You can also use "XML" if needed
                    }
                },
                {
                    "topic": "DISCOUNTS_UPDATE",  # Event for product updates
                    "webhookSubscription": {
                        "callbackUrl": callback_url+'/webhook/coupen',
                        "format": "JSON"  # You can also use "XML" if needed
                    }
                },
                {
                    "topic": "ORDERS_CREATE",  # Event for product updates
                    "webhookSubscription": {
                        "callbackUrl": callback_url+'/webhook/order',
                        "format": "JSON"  # You can also use "XML" if needed
                    }
                },
                {
                    "topic": "ORDERS_UPDATED",  # Event for product updates
                    "webhookSubscription": {
                        "callbackUrl": callback_url+'/webhook/order',
                        "format": "JSON"  # You can also use "XML" if needed
                    }
                }
            ]

            for webhook_input in webhooks_input:

                # Build the GraphQL request payload
                payload = {
                    "query": mutation,
                    "variables": webhook_input
                }

                response = requests.post(shop_url, headers=headers, json=payload)

                # Handle the response
                if response.status_code == 200:
                    data = response.json()
                    _logger.info("webhook subscription: %s", json.dumps(data))
                    if data.get("errors"):
                        raise Exception(f"GraphQL errors: {data['errors']}")
                    webhook_ref_id = data["data"]["webhookSubscriptionCreate"]["webhookSubscription"]['id']
                    field_name = helper.topic_mapping_field(webhook_input["topic"])
                    if field_name:
                        setattr(record, field_name, webhook_ref_id)
                    #return data["data"]["webhookSubscriptionCreate"]
                else:
                    raise Exception(f"HTTP error {response.status_code}: {response.text}")
    
    @api.model
    def get_base_url(self):
        """
        Retrieve the current base URL of the Odoo instance.
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return base_url
    
    def prepare_product_queue(self):
        for rec in self:
            #rec.import_shopify_products()

            sync_obj = {
                'type' : 'product',
                'shopify_store' : rec.id             
            }
            
            queue = self.env['shopify.sync.queue'].create(sync_obj)
            if queue:
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Product queue added'),
                        'type': 'success',
                        'message': 'Product queue added in module',
                        'sticky': False,
                    }
                }
            else:
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Failed'),
                        'type': 'warning',
                        'message': 'Something went wrong',
                        'sticky': False,
                    }
                }
            return notification
    
    def prepare_customer_queue(self):
        for rec in self:

            sync_obj = {
                'type' : 'customer',
                'shopify_store' : rec.id             
            }
            
            queue = self.env['shopify.sync.queue'].create(sync_obj)
            if queue:
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Customer queue added'),
                        'type': 'success',
                        'message': 'Customer queue added in module',
                        'sticky': False,
                    }
                }
            else:
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Failed'),
                        'type': 'warning',
                        'message': 'Something went wrong',
                        'sticky': False,
                    }
                }
            return notification
    
    def prepare_order_queue(self):
        for rec in self:

            sync_obj = {
                'type' : 'order',
                'shopify_store' : rec.id             
            }
            
            queue = self.env['shopify.sync.queue'].create(sync_obj)
            if queue:
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Order queue added'),
                        'type': 'success',
                        'message': 'Order queue added in module',
                        'sticky': False,
                    }
                }
            else:
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Failed'),
                        'type': 'warning',
                        'message': 'Something went wrong',
                        'sticky': False,
                    }
                }
            return notification
    
       
    # Cron Function
    def sync_product_cron(self):
        _logger.info("Product Cron called")
        # shopify_connectors = self.env['shopify.connector'].search([])
        # for shopify_connector in shopify_connectors:
        #     _logger.info("Product Cron")
        #     shopify_connector.import_shopify_products()

    def sync_customer_cron(self):
        shopify_connectors = self.env['shopify.connector'].search([])
        for shopify_connector in shopify_connectors:
            _logger.info("Customer Cron")
            shopify_connector.import_shopify_customer()


# gid://shopify/DiscountCodeNode/1264647700611

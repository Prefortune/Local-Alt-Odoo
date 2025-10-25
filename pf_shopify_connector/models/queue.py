from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import time
import requests
from odoo.exceptions import ValidationError,UserError
import json

class ShopifySyncQueue(models.Model):
    _name = 'shopify.sync.queue'
    _description = 'Shopify Sync Queue'

    type = fields.Selection([
        ('product', 'Product'),
        ('customer', 'Customer'),
        ('order', 'Order'),
    ], string='Queue Type', required=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed')
    ], default='pending', string='Status', required=True)
    error_message = fields.Text(string='Error Message')
    sync_attempts = fields.Integer(string='Sync Attempts', default=0)
    next_cursor = fields.Char(string="Next cursor")
    shopify_store = fields.Many2one('shopify.connector',string="Shopify store",required=True)

    # Cron Function
    def sync_product_cron(self):
        _logger.info("Product Cron start")
        start = time.time()
        helper = self.env['helper.utils']
        cron_name = "pf_shopify_connector.sync_product_auto"
        process_cron_time = helper.get_cron_execution_time(cron_name)
        # shopify_connectors = self.env['shopify.connector'].search([])
        # for shopify_connector in shopify_connectors:
        #     _logger.info("Product Cron")
        #     shopify_connector.import_shopify_products()

        records = self.search([('type','=','product'),('state','in',['pending','processing'])])
        for rec in records:
            self._cr.commit()
            rec.state = 'processing'
            connection_status = rec.shopify_store.test_shopify_connection()
            
            if connection_status == 'Connection success':
                shop_url = rec.shopify_store.shopify_url

                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": rec.shopify_store.shopify_access_token
                }
                
                # Dynamic number of products to fetch
                first_products = 10  # This can be dynamically set as needed
                has_next_page = True
                cursor = None  # Initially no cursor
                if rec.next_cursor:
                    cursor = rec.next_cursor
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

                    try:

                        # Make the POST request to Shopify GraphQL API
                        response = requests.post(shop_url, json={'query': query, 'variables': variables}, headers=headers)
                        
                        # Log the response
                        if response.status_code == 200:
                            products_data = response.json()
                            # _logger.info("Data: %s", json.dumps(products_data))
                            
                            # Process products here (products_data['products_data']['products']['nodes'])
                            products = products_data['data']['products']['nodes']
                            #_logger.info("products: %s", json.dumps(products))
                            #all_products.extend(products)
                            # Example: Add products to the system, or do further processing
                            
                            # Check for pagination
                            page_info = products_data['data']['products']['pageInfo']
                            has_next_page = page_info['hasNextPage']
                            
                            # Set the cursor for the next page

                            sync_type = "sync_button"
                            shopify_product = rec.env['shopify.product']
                            shopify_product.sync_product(products, rec.shopify_store, sync_type)

                            if has_next_page:
                                cursor = page_info['endCursor']
                            else:
                                cursor = None  # No more pages
                                rec.state = 'done'
                            rec.next_cursor = cursor

                            _logger.info("time.time() %s",time.time())
                            _logger.info("start %s",start)
                            _logger.info("process_cron_time - 60 %s",process_cron_time - 60)
                            self._cr.commit()
                            if time.time() - start > process_cron_time - 60:
                                _logger.info("Product Cron stopped")
                                return True

                        else:
                            _logger.error("Error fetching data: %s", response.text)
                            #raise ValidationError(_('Error fetching data'))
                            rec.state = 'failed'  # Set the state to 'error' to mark the record as failed
                            rec.error_message = 'Error fetching data'
                            break  # Exit the loop if an error occurs
                    
                    except Exception as e:
                        _logger.error("An error occurred: %s", str(e))
                        rec.state = 'failed'  # Set the state to 'error' to mark the record as failed
                        rec.error_message = str(e)
                        break  # Exit the loop on error
                #_logger.info(" all products: %s", json.dumps(all_products))

        _logger.info("Product Cron completed")
        return True

    # Cron Function
    def sync_customer_cron(self):
        _logger.info("Customer Cron start")
        start = time.time()
        helper = self.env['helper.utils']
        cron_name = "pf_shopify_connector.sync_customer_auto"
        process_cron_time = helper.get_cron_execution_time(cron_name)
        # shopify_connectors = self.env['shopify.connector'].search([])
        # for shopify_connector in shopify_connectors:
        #     _logger.info("Product Cron")
        #     shopify_connector.import_shopify_products()

        records = self.search([('type','=','customer'),('state','in',['pending','processing'])])
        for rec in records:
            self._cr.commit()
            rec.state = 'processing'
            connection_status = rec.shopify_store.test_shopify_connection()
            
            if connection_status == 'Connection success':
                shop_url = rec.shopify_store.shopify_url

                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": rec.shopify_store.shopify_access_token
                }
                
                # Dynamic number of products to fetch
                first_customer = 5  # This can be dynamically set as needed
                has_next_page = True
                cursor = None  # Initially no cursor
                if rec.next_cursor:
                    cursor = rec.next_cursor

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
                        #all_customers.extend(customers)
                        # Example: Add products to the system, or do further processing
                        
                        # Check for pagination
                        page_info = customers_data['data']['customers']['pageInfo']
                        has_next_page = page_info['hasNextPage']

                        sync_type = "sync_button"
                        shopify_customer = rec.env['shopify.customer']
                        shopify_customer.sync_customer(customers, rec.shopify_store, sync_type)
                        
                        if has_next_page:
                            cursor = page_info['endCursor']
                        else:
                            cursor = None  # No more pages
                            rec.state = 'done'
                        rec.next_cursor = cursor

                        _logger.info("time.time() %s",time.time())
                        _logger.info("start %s",start)
                        _logger.info("process_cron_time - 60 %s",process_cron_time - 60)
                        self._cr.commit()
                        if time.time() - start > process_cron_time - 60:
                            _logger.info("Customer Cron stopped")
                            return True

                    else:
                        _logger.error("Error fetching data: %s", response.text)
                        #raise ValidationError(_('Error fetching data'))
                        rec.state = 'failed'  # Set the state to 'error' to mark the record as failed
                        rec.error_message = 'Error fetching data'
                        break  # Exit the loop if an error occurs

        _logger.info("Customer Cron completed")
        return True


    # Cron Function
    def sync_order_cron(self):
        _logger.info("Order Cron start")
        start = time.time()
        helper = self.env['helper.utils']
        cron_name = "pf_shopify_connector.sync_order_auto"
        process_cron_time = helper.get_cron_execution_time(cron_name)
        # shopify_connectors = self.env['shopify.connector'].search([])
        # for shopify_connector in shopify_connectors:
        #     _logger.info("Product Cron")
        #     shopify_connector.import_shopify_products()

        records = self.search([('type','=','order'),('state','in',['pending','processing'])])
        for rec in records:
            self._cr.commit()
            rec.state = 'processing'
            connection_status = rec.shopify_store.test_shopify_connection()
            
            if connection_status == 'Connection success':
                shop_url = rec.shopify_store.shopify_url

                # Set the headers with the access token
                headers = {
                    "Content-Type": "application/json",  # Correct header
                    "X-Shopify-Access-Token": rec.shopify_store.shopify_access_token
                }
                
                # Dynamic number of products to fetch
                first_order = 10  # This can be dynamically set as needed
                has_next_page = True
                cursor = None  # Initially no cursor
                if rec.next_cursor:
                    cursor = rec.next_cursor

                while has_next_page:
                    # GraphQL query with dynamic variable for `first` and `after` (cursor)
                    query = """
                        query ($first: Int!, $after: String) {
                            orders(first: $first, after: $after, sortKey: ID) {
                                nodes {
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
                        
                        # Check for pagination
                        page_info = orders_data['data']['orders']['pageInfo']
                        has_next_page = page_info['hasNextPage']

                        sync_type = "sync_button"
                        shopify_order = rec.env['shopify.order']
                        shopify_order.sync_order(orders, shop_url, rec.shopify_store, sync_type)
                        
                        # Set the cursor for the next page
                        if has_next_page:
                            cursor = page_info['endCursor']
                        else:
                            cursor = None  # No more pages
                            rec.state = 'done'
                        rec.next_cursor = cursor

                        _logger.info("time.time() %s",time.time())
                        _logger.info("start %s",start)
                        _logger.info("process_cron_time - 60 %s",process_cron_time - 60)
                        self._cr.commit()
                        if time.time() - start > process_cron_time - 60:
                            _logger.info("Order Cron stopped")
                            return True

                    else:
                        _logger.error("Error fetching data: %s", response.text)
                        #raise ValidationError(_('Error fetching data'))
                        rec.state = 'failed'  # Set the state to 'error' to mark the record as failed
                        rec.error_message = 'Error fetching data'
                        return True  # Exit the loop if an error occurs

        _logger.info("Order Cron completed")
        return True
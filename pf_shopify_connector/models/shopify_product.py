from odoo import api, fields, models
import requests
from odoo.exceptions import ValidationError,UserError
from itertools import product
import base64
import json
from odoo.tools.float_utils import float_compare, float_is_zero

import logging
_logger = logging.getLogger(__name__)

class ShopifyProduct(models.Model):
    _name = "shopify.product"
    _description = "Shopify Product"

    # name = fields.Char(string="Store Name")

    def create_attribute_if_not_exists(self, attribute_name):
        attribute_data = self.env['product.attribute'].search([('name', '=', attribute_name)])

        if not attribute_data:
            create_attribute = self.env['product.attribute'].create({'name': attribute_name})
            return create_attribute.id
        else:
            return attribute_data.id

    def create_value_if_not_exists(self, attribute_id, attribute_value):
        value_data = self.env['product.attribute.value'].search([
            ('attribute_id', '=', attribute_id),
            ('name', '=', attribute_value)
        ])

        if not value_data:
            create_value = self.env['product.attribute.value'].create({
                'attribute_id': attribute_id,
                'name': attribute_value
            })
            return create_value.id
        else:
            return value_data.id
  
    def sync_product(self, products, shopify_connector, sync_type):
        product_template = self.env['product.template']
        product_product = self.env['product.product']
        product_category = self.env['product.category']
        _logger.info("sync shopify product %s", products)
        existing_products = self.env['product.template'].search([('is_shopify_product', '=', True),('shopify_store', '=', shopify_connector.id)])
        exclude_ids = []
        # for ex_pro in existing_products:
        #     exclude_ids.append(ex_pro.shopify_product_id)
        # _logger.info("this is all ids exist in odoo %s", exclude_ids)
        self = self.with_context(def_name='sync_product')
        for product in products:
            # if str(product['id']) in exclude_ids and sync_type == "sync_button":
            #     _logger.info("This is match ids %s", product['id'])
            #     continue
            product_id = product['id'].split("/")[-1]
            _logger.info("This is product id %s ", product_id)
            
            shopify_qraphql_product_id = product['id']
            product_name = product['title']
            product_description = product['descriptionHtml']

            find_exists = product_template.search([('shopify_product_id', '=', product_id),('shopify_store', '=', shopify_connector.id)])
            product_category_name = product['productCategory']['productTaxonomyNode']['fullName'] if product['productCategory'] else 'All'
            if product_category_name:
                _logger.info("Product category: %s", product_category_name)
                
                # Split the full category name into parts
                category_parts = product_category_name.split(' > ')
                parent_category_id = False  # Initialize the parent category ID as None or False
                
                for category_name in category_parts:
                    # Search for the category with the current name and parent
                    find_product_category_exists = product_category.search([
                        ('name', '=', category_name),
                        ('parent_id', '=', parent_category_id)
                    ])
                    
                    if find_product_category_exists:
                        # If category exists, use its ID as the parent for the next level
                        product_category_id = find_product_category_exists.id
                    else:
                        # Create the category with the current parent ID
                        create_product_category = product_category.create({
                            'name': category_name,
                            'parent_id': parent_category_id
                        })
                        _logger.info("Created product category: %s", create_product_category)
                        product_category_id = create_product_category.id
                    
                    # Update parent_category_id for the next iteration
                    parent_category_id = product_category_id

            product_dict = {
                'name': product_name,
                'detailed_type': 'product',
                'list_price': 0 if product['totalVariants'] > 1 else product["priceRangeV2"]["minVariantPrice"]["amount"],
                'shopify_product_id': product_id,
                'shopify_qraphql_product_id': shopify_qraphql_product_id,
                'description': product_description,
                'categ_id': product_category_id,
                'available_in_pos': True,
                'company_id':self.env.company.id
            }

            if product['featuredMedia']:
                image_test = product['featuredMedia']['preview']['image']['src']
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(image_test, headers=headers)
                base64_data = base64.b64encode(response.content).decode('utf-8')
                product_dict['image_1920'] = base64_data

            attribute_line_data = {}

            for attr in product['options']:
                attribute_name = attr['name']
                values = [value.strip() for value in attr['values']]
                
                if attribute_name == "Title":
                    _logger.info("This is Title %s", product_id)
                    continue

                attribute_id = self.create_attribute_if_not_exists(attribute_name)

                attribute_line_data[attribute_id] = [self.create_value_if_not_exists(attribute_id, value) for value in values]

            # Create Attribute Line For Product Variant
            attribute_line_ids = [
                (0, 0, {'attribute_id': attr_id, 'value_ids': [(6, 0, attr_values)]})
                for attr_id, attr_values in attribute_line_data.items()
            ]

            # Create Product or Update Product
            if attribute_line_ids:
                product_dict['attribute_line_ids'] = attribute_line_ids

            if find_exists:
                _logger.info("This is find_exists %s", find_exists)
                existing_attr_line_id = find_exists.attribute_line_ids

                if existing_attr_line_id:
                    for attr_id, val_array in attribute_line_data.items():
                        existing_attr_temp_val_data = self.env['product.template.attribute.line'].search([
                            ('attribute_id', '=', attr_id),
                            ('product_tmpl_id', '=', find_exists.id)
                        ])
                        # Update Attribute Value If availble else create new attribute
                        if existing_attr_temp_val_data:
                            existing_attr_temp_val_data.write({'attribute_id': attr_id, 'value_ids': [(4, val) for val in val_array]})
                            product_dict['attribute_line_ids'] = []
                        else:
                            new_attr_data = (0, 0, {'attribute_id': attr_id, 'value_ids': [(6, 0, val_array)]})
                            product_dict['attribute_line_ids'] = [new_attr_data]

                    product_update = find_exists.with_context(def_name='sync_product').write(product_dict)
                else:
                    if attribute_line_ids:
                        product_dict['attribute_line_ids'] = attribute_line_ids
                    product_update = find_exists.with_context(def_name='sync_product').write(product_dict)
                
                if product_update:
                    product_template_id = find_exists
            else:
                _logger.info("THis is CRaete PRoduct template")
                product_create = product_template.with_context(def_name='sync_product').create(product_dict)

                if product_create:
                    product_create.with_context(def_name='sync_product').write({'is_shopify_product':True,'shopify_store':shopify_connector})
                    product_template_id = product_create
            
            # Add shopify_product_id and shopify_product_variant_id to product.product 
            find_exists_variant = product_template.search([('id', '=', product_template_id.id)])

            _logger.info("find_exists_variant %s", len(find_exists_variant['product_variant_ids']))
            _logger.info("product %s", product['totalVariants'])
            
            #if len(find_exists_variant['product_variant_ids']) == product['totalVariants']:
            #_logger.info("same length product_variant %s", find_exists_variant.shopify_product_id)
            self._update_variant_data(find_exists_variant, product, shopify_connector.store_price_list, shopify_connector)
                   
    def post_product(self, values, template_id, shopify_store_id):
        shopify_store = self.env['shopify.connector']
        shopify_store_data = shopify_store.search([('id', '=', shopify_store_id)])
        shop_url = shopify_store_data.shopify_url
        store_price_list = shopify_store_data.store_price_list
        shopify_access_token = shopify_store_data.shopify_access_token

        product_name = values['name']
        sales_price = values['list_price']
        product_description = values['description']

        shopify_product_dict = {
            "product": {
                "title": product_name,
                "descriptionHtml": product_description,
            }
        }
        
        if 'image_1920' in values:
            shopify_product_dict['product']['images'] = [
                {
                    "attachment": values['image_1920'],
                    "filename": product_name + ".jpg"  # Change the filename as needed
                }
            ]
        variant_combination = []  # Initialize an empty list to store result variants
        attribute_values_list = []  # Initialize a list to store attribute values
        option_names = []  # List of option names (e.g., "Color", "Size")
        formatted_output = []
        formatted_option_names = []
        if values['attribute_line_ids']:
            for attribute_line in values.get('attribute_line_ids', []):
                if isinstance(attribute_line[1], str):
                    odoo_attribute_id = attribute_line[2].get('attribute_id')
                    attribute_id = self._get_attribute_details(odoo_attribute_id)
                    value_ids = attribute_line[2].get('value_ids')

                    if value_ids is not None:
                        # Extract the second element of each pair in value_ids
                        value_list = [value[1] for value in value_ids if len(value) > 1]
                        attribute_values = [
                            self._get_attribute_value_details(attribute_id, atr_val) for atr_val in value_list
                        ]
                        attribute_values_list.append(attribute_values)
                        option_names.append(attribute_id)
                    else:
                        _logger.warning("No value_ids found for attribute line: %s", attribute_line)

            # Generate combinations using itertools.product
            combinations = product(*attribute_values_list)

            for combination in combinations:
                variant = {
                    f"options": list(combination),  # Each combination becomes a list of options
                    f"price": sales_price,
                }
                variant_combination.append(variant)

            # Add variants and options to the product dictionary
            # shopify_product_dict["product"]["variants"] = variant_combination
            # shopify_product_dict["product"]["options"] = option_names
            formatted_output = json.dumps(variant_combination)
            # Remove quotes from dictionary keys
            formatted_output = formatted_output.replace('"options":', 'options:').replace('"price":', 'price:')
            formatted_option_names = json.dumps(option_names)
            

        # Create the GraphQL mutation string
        operation_type = 'productCreate'
        create_or_update_shopify_product = self._create_or_update_shopify_product(template_id, operation_type, formatted_output, formatted_option_names, shopify_store_id)
        # shopify_graphql_dict = f"""
        #     mutation {{
        #         productCreate(
        #             input: {{
        #                 title: "{product_name}"
        #                 descriptionHtml: "{product_description}"
        #                 variants: {formatted_output}
        #                 options: {formatted_option_names}
        #             }}
        #         ) {{
        #             product {{
        #                 id
        #                 title
        #                 totalVariants
        #                 variants(first: 100) {{
        #                     nodes {{
        #                         id
        #                         displayName
        #                         price
        #                         title
        #                         inventoryQuantity
        #                         image {{
        #                             id
        #                             src
        #                             url
        #                         }}
        #                     }}
        #                 }}
        #             }}
        #             userErrors {{
        #                 field
        #                 message
        #             }}
        #         }}
        #     }}
        # """

        # _logger.info("graphql dict %s", shopify_graphql_dict)
        # # Set the headers with the access token
        # headers = {
        #     "Content-Type": "application/json",  # Correct header
        #     "X-Shopify-Access-Token": shopify_access_token
        # }

        # # response = requests.post(shop_url +"/products.json", json=shopify_product_dict)
        # response = requests.post(shop_url, json={'query': shopify_graphql_dict}, headers=headers)
        # _logger.info("response %s", response.status_code)
        # _logger.info("response Json %s", response.json())
        # if response.status_code == 200:
        #     _logger.info("this is new created shopify product %s", response.json())
        #     shopify_created_product = response.json()['data']['productCreate']['product']
        #     product_id = shopify_created_product['id'].split("/")[-1]
        #     shopify_qraphql_product_id = shopify_created_product['id']
        #     template_id.write({'shopify_product_id':product_id,'shopify_qraphql_product_id': shopify_qraphql_product_id,})

        #     _logger.info("template_id['product_variant_ids'] %s", len(template_id['product_variant_ids']))
        #     _logger.info("shopify_created_product['variants'] %s", shopify_created_product['totalVariants'])
        #     if len(template_id['product_variant_ids']) == shopify_created_product['totalVariants']:
        #         _logger.info("There is variant length match ")
        #         self._update_variant_data(template_id, shopify_created_product, store_price_list, shopify_store_data)  

    def _get_attribute_details(self, attribute_id):
         attribute_data = self.env['product.attribute'].search([('id', '=', attribute_id)])
         return attribute_data.name
    
    def _get_attribute_value_details(self, attribute_id, value_id):
        value_data = self.env['product.attribute.value'].search([('attribute_id', '=', attribute_id),('id', '=', value_id)])
        return value_data.name
    
    def _update_variant_data(self, product_template, shopify_product, store_price_list, shopify_connector):
        product_product = self.env['product.product']
        variant_data = product_product.search([('product_tmpl_id', '=', product_template.id)])
        if len(variant_data.product_template_attribute_value_ids) > 1:
            for variant in variant_data:
                # Extract attribute names from variant
                variant_names = [rec.name for rec in variant.product_template_attribute_value_ids]
                _logger.info("odoo_variant_names %s",variant_names)
                for shopify_variant in shopify_product['variants']['nodes']:
                    _logger.info('shopify_variant %s',shopify_variant)
                    shopify_title = shopify_variant['title']
                    shopify_qraphql_product_variant_id = shopify_variant['id']
                    shopify_variant_id = shopify_variant['id'].split("/")[-1]
                    # Compare variant_names with shopify_title
                    shopify_variant_name = [names.strip() for names in shopify_title.split(' / ')]
                    _logger.info("shopify_variant_name %s",shopify_variant_name)
                    #if all(item in variant_names for item in shopify_variant_name):
                    if sorted(variant_names) == sorted(shopify_variant_name):
                        variant_update_dict = {
                            'shopify_variant_id': shopify_variant_id,
                            'shopify_qraphql_product_variant_id': shopify_qraphql_product_variant_id,
                            'shopify_product_id': shopify_product['id'].split("/")[-1],
                            'shopify_qraphql_product_id': shopify_product['id'],
                            'shopify_store': shopify_connector.id,
                            'default_code': shopify_variant['sku'],
                            'company_id':self.env.company.id
                        }

                        if shopify_variant['image']:
                            _logger.info("variant id for image %s", shopify_variant_id)
                            variant_image_src = shopify_variant['image']['src']
                            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                            response = requests.get(variant_image_src, headers=headers)
                            base64_data = base64.b64encode(response.content).decode('utf-8')
                            variant_update_dict['image_variant_1920'] = base64_data
                        _logger.info("variant_update_data for %s data %s",variant,variant_update_dict)
                        if not shopify_connector.is_price_list_require:
                            variant_update_dict['custom_price_extra'] = shopify_variant['price']
                            update_variant = variant.write(variant_update_dict)
                        else:
                            update_variant = variant.write(variant_update_dict)
                            self._update_variant_combination_price(variant, shopify_variant['price'], store_price_list)
        else:
            shopify_variant = shopify_product['variants']['nodes'][0]
            shopify_qraphql_product_variant_id = shopify_product['variants']['nodes'][0]['id']
            shopify_variant_id = shopify_variant['id'].split("/")[-1]
            product_id = shopify_product['id'].split("/")[-1]
            shopify_qraphql_product_id = shopify_product['id']
            variant_update_dict = {
                'shopify_variant_id': shopify_variant_id,
                'shopify_qraphql_product_variant_id': shopify_qraphql_product_variant_id,
                'shopify_product_id': product_id,
                'shopify_qraphql_product_id': shopify_qraphql_product_id,
                'shopify_store': shopify_connector.id,
                'company_id':self.env.company.id
            }
            update_variant = variant_data.write(variant_update_dict)
            self._update_variant_combination_price(variant_data, shopify_product['variants']['nodes'][0]['price'], store_price_list)
        #self._update_stock(shopify_product, shopify_connector)

    def put_product(self, values, template_id, shopify_store_id):
        shop_url = shopify_store_id.shopify_url
        store_price_list = shopify_store_id.store_price_list
        shopify_access_token = shopify_store_id.shopify_access_token

        shopify_product_dict = {
            "product": {
                "title": template_id.name,
                "body_html": template_id.description,
            }
        }

        if 'image_1920' in values:
            shopify_product_dict['product']['images'] = [
                {
                    "attachment": values['image_1920'],
                    "filename": template_id.name + ".jpg"  # Change the filename as needed
                }
            ]

        shopify_product_id = template_id.shopify_product_id
        variant_combination = []  # Initialize an empty list to store result variants
        attribute_values_list = []  # Initialize a list to store attribute values
        option_names = []  # List of option names (e.g., "Color", "Size")
        formatted_output = []
        formatted_option_names = []
        if template_id.attribute_line_ids:
            _logger.info("attribtes list %s", template_id.attribute_line_ids)
            for attribute_line in template_id.attribute_line_ids:
                _logger.info("attribute_line %s", attribute_line)
                # _logger.info("attribute_line[1] %s", attribute_line[1])
                # if isinstance(attribute_line, str):
                odoo_attribute_id = attribute_line.attribute_id
                _logger.info("odoo_attribute_id %s", odoo_attribute_id)
                attribute_id = self._get_attribute_details(odoo_attribute_id.id)
                _logger.info("attribute_id %s", attribute_id)
                value_ids = attribute_line.value_ids
                _logger.info("value_ids %s", value_ids)

                if value_ids is not None:

                    # Extract the second element of each pair in value_ids
                    # value_list = [value.id for value in value_ids if len(value) > 1]
                    value_list = [value.id for value in value_ids if value.id]
                    _logger.info("value_list %s", value_list)
                    attribute_values = [
                        self._get_attribute_value_details(attribute_id, atr_val) for atr_val in value_list
                    ]
                    attribute_values_list.append(attribute_values)
                    option_names.append(attribute_id)
                else:
                    _logger.warning("No value_ids found for attribute line: %s", attribute_line)

            # Generate combinations using itertools.product
            combinations = product(*attribute_values_list)

            for combination in combinations:
                variant = {
                    f"options": list(combination),  # Each combination becomes a list of options
                }
                variant_combination.append(variant)
            
            _logger.info("variant_combination check %s", variant_combination)

            # Add variants and options to the product dictionary
            # shopify_product_dict["product"]["variants"] = variant_combination
            # shopify_product_dict["product"]["options"] = option_names
            formatted_output = json.dumps(variant_combination)
            # Remove quotes from dictionary keys
            formatted_output = formatted_output.replace('"options":', 'options:')
            formatted_option_names = json.dumps(option_names)
            

        # Create the GraphQL mutation string
        operation_type = 'productUpdate' if shopify_product_id else 'productCreate'
        create_or_update_shopify_product = self._create_or_update_shopify_product(template_id, operation_type, formatted_output, formatted_option_names, shopify_store_id.id)
        # shopify_graphql_dict = f"""
        #     mutation {{
        #         {operation_type}(
        #             input: {{
        #                 {id_field}
        #                 title: "{template_id.name}"
        #                 descriptionHtml: "{template_id.description}"
        #                 variants: {formatted_output}
        #                 options: {formatted_option_names}
        #             }}
        #         ) {{
        #             product {{
        #                 id
        #                 title
        #                 totalVariants
        #                 variants(first: 100) {{
        #                     nodes {{
        #                         id
        #                         displayName
        #                         price
        #                         title
        #                         inventoryQuantity
        #                         image {{
        #                             id
        #                             src
        #                             url
        #                         }}
        #                     }}
        #                 }}
        #             }}
        #             userErrors {{
        #                 field
        #                 message
        #             }}
        #         }}
        #     }}
        # """

        # _logger.info("graphql dict %s", shopify_graphql_dict)
        # # Set the headers with the access token
        # headers = {
        #     "Content-Type": "application/json",  # Correct header
        #     "X-Shopify-Access-Token": shopify_access_token
        # }
        # response = requests.post(shop_url, json={'query': shopify_graphql_dict}, headers=headers)
        # _logger.info("response %s", response.status_code)
        # _logger.info("response Json %s", response.json())
        # if response.status_code == 200:
        #     _logger.info("this is new created shopify product %s", response.json())
        #     shopify_created_product = response.json()['data'][operation_type]['product']
        #     product_id = shopify_created_product['id'].split("/")[-1]
        #     shopify_qraphql_product_id = shopify_created_product['id']
        #     template_id.write({'shopify_product_id':product_id,'shopify_qraphql_product_id': shopify_qraphql_product_id,})

        #     _logger.info("template_id['product_variant_ids'] %s", len(template_id['product_variant_ids']))
        #     _logger.info("shopify_created_product['variants'] %s", shopify_created_product['totalVariants'])
        #     if len(template_id['product_variant_ids']) == shopify_created_product['totalVariants']:
        #         _logger.info("There is variant length match ")
        #         self._update_variant_data(template_id, shopify_created_product, store_price_list, shopify_store_id)

    def _get_attr_id_from_attr_line(self, template_id, attr_line_id):
        atr_line_data = self.env['product.template.attribute.line'].search([('id', '=', attr_line_id)])
        return atr_line_data.attribute_id, atr_line_data.value_ids

    def _update_stock(self, shopify_product, shopify_connector):
        location_data = self.env['stock.location'].sudo().search([('usage', '=', 'internal')], limit=1) 
        location_id = int(location_data)
        shopify_variant_ids = shopify_product['variants']['nodes']
        for varaint in shopify_variant_ids:
            shopify_qraphql_product_variant_id = varaint['id']
            varaint_id = varaint['id'].split("/")[-1]
            _logger.info("varaint_id_of_stock %s",varaint_id)          
            product_variant_id = self.env['product.product'].sudo().search([('shopify_variant_id', '=', varaint_id),('shopify_qraphql_product_variant_id', '=', shopify_qraphql_product_variant_id),('shopify_store', '=', shopify_connector.id)])
            if product_variant_id:
                quantity = varaint['inventoryQuantity']
                existing_quant = self.env['stock.quant'].sudo().search([('product_id', '=', product_variant_id.id),('location_id', '=', location_id)])
                if existing_quant:                            
                    update_quantity = existing_quant.sudo().write({'inventory_quantity': quantity})
                    update_id = existing_quant.id
                else:
                    stock_update_data = {
                        'product_id': product_variant_id.id,
                        'inventory_quantity': quantity,
                        'inventory_quantity_set': True,
                        'location_id': location_id,
                    }
                    _logger.info("stock_update_data %s",stock_update_data)
                    update_quantity = self.env['stock.quant'].sudo().create(stock_update_data)
                    update_id = update_quantity.id

                if update_quantity:
                    adjustment_name_vals = {
                        'quant_ids': [(6, 0, [update_id])],  # Pass quant_ids as a list of IDs
                    }
                    adjustment_name = self.env['stock.inventory.adjustment.name'].sudo().create(adjustment_name_vals)
                    update_stock_action_apply = adjustment_name.sudo().action_apply()
               
    def _update_variant_combination_price(self, variant, shopify_product_combination_price, store_price_list):
        _logger.info("_update_variant_combination_price")
        product_pricelist_item = self.env['product.pricelist.item']
        existing_product_pricelist_item = product_pricelist_item.search([('product_id', '=', variant.id)])
        values = {
            'product_tmpl_id': variant.product_tmpl_id.id,
            'product_id': variant.id,
            'pricelist_id': store_price_list.id,
            'fixed_price': shopify_product_combination_price,
            "applied_on": "0_product_variant",
        }
        if existing_product_pricelist_item:
            update_woo_variant_price = existing_product_pricelist_item.write(values)
        else:
            create_woo_variant_price = product_pricelist_item.create(values)

    def _shopify_variant_price_update(self, product_variant_id, values, shopify_store):
        shopify_produt_variant_id = product_variant_id.shopify_variant_id
        _logger.info(shopify_produt_variant_id)
        combination_price = values['fixed_price']
        shop_url = shopify_store.shopify_url
        update_price = {
            "variant": {
                "price": str(combination_price)
            }
        }
        response = requests.put(shop_url +"/variants/" + shopify_produt_variant_id + ".json", json=update_price)

    def _create_or_update_shopify_product(self, template_id, operation_type, formatted_output, formatted_option_names, shopify_store_id):
        shopify_store = self.env['shopify.connector']
        shopify_store_data = shopify_store.search([('id', '=', shopify_store_id)])
        shop_url = shopify_store_data.shopify_url
        store_price_list = shopify_store_data.store_price_list
        shopify_access_token = shopify_store_data.shopify_access_token

        id_field = f'id: "{template_id.shopify_qraphql_product_id}",' if template_id.shopify_product_id else ""
        shopify_graphql_dict = f"""
        mutation {{
            {operation_type}(
                input: {{
                    {id_field}
                    title: "{template_id.name}"
                    descriptionHtml: "{template_id.description}"
                    variants: {formatted_output}
                    options: {formatted_option_names}
                }}
            ) {{
                product {{
                    id
                    title
                    totalVariants
                    variants(first: 100) {{
                        nodes {{
                            id
                            displayName
                            price
                            title
                            sku
                            inventoryQuantity
                            image {{
                                id
                                src
                                url
                            }}
                        }}
                    }}
                }}
                userErrors {{
                    field
                    message
                }}
            }}
        }}
        """

        _logger.info("graphql dict %s", shopify_graphql_dict)
        # Set the headers with the access token
        headers = {
            "Content-Type": "application/json",  # Correct header
            "X-Shopify-Access-Token": shopify_access_token
        }
        response = requests.post(shop_url, json={'query': shopify_graphql_dict}, headers=headers)
        _logger.info("response %s", response.status_code)
        _logger.info("response Json %s", response.json())
        if response.status_code == 200:
            _logger.info("this is new created shopify product %s", response.json())
            self._update_variants_after_shopify_create(response, template_id, operation_type, store_price_list, shopify_store_data)
            # shopify_created_product = response.json()['data'][operation_type]['product']
            # product_id = shopify_created_product['id'].split("/")[-1]
            # shopify_qraphql_product_id = shopify_created_product['id']
            # template_id.write({'shopify_product_id':product_id,'shopify_qraphql_product_id': shopify_qraphql_product_id,})

            # _logger.info("template_id['product_variant_ids'] %s", len(template_id['product_variant_ids']))
            # _logger.info("shopify_created_product['variants'] %s", shopify_created_product['totalVariants'])
            # if len(template_id['product_variant_ids']) == shopify_created_product['totalVariants']:
            #     _logger.info("There is variant length match ")
            #     self._update_variant_data(template_id, shopify_created_product, store_price_list, shopify_store_data)

    def _update_variants_after_shopify_create(self, response, template_id, operation_type, store_price_list, shopify_store_data):
        shopify_created_product = response.json()['data'][operation_type]['product']
        product_id = shopify_created_product['id'].split("/")[-1]
        shopify_qraphql_product_id = shopify_created_product['id']
        template_id.write({'shopify_product_id':product_id,'shopify_qraphql_product_id': shopify_qraphql_product_id,})

        _logger.info("template_id['product_variant_ids'] %s", len(template_id['product_variant_ids']))
        _logger.info("shopify_created_product['variants'] %s", shopify_created_product['totalVariants'])
        if len(template_id['product_variant_ids']) == shopify_created_product['totalVariants']:
            _logger.info("There is variant length match ")
            self._update_variant_data(template_id, shopify_created_product, store_price_list, shopify_store_data)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _apply_inventory(self):
        move_vals = []
        if not self.user_has_groups('stock.group_stock_manager') and not self.env.user._is_public():
            raise UserError(_('Only a stock manager can validate an inventory adjustment.'))
        for quant in self:
            # Create and validate a move so that the quant matches its `inventory_quantity`.
            if float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0:
                move_vals.append(
                    quant._get_inventory_move_values(quant.inventory_diff_quantity,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     quant.location_id, package_dest_id=quant.package_id))
            else:
                move_vals.append(
                    quant._get_inventory_move_values(-quant.inventory_diff_quantity,
                                                     quant.location_id,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     package_id=quant.package_id))
        moves = self.env['stock.move'].with_context(inventory_mode=False).create(move_vals)
        moves._action_done()
        self.location_id.write({'last_inventory_date': fields.Date.today()})
        date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
        for quant in self:
            quant.inventory_date = date_by_location[quant.location_id]
        self.write({'inventory_quantity': 0, 'user_id': False})
        self.write({'inventory_diff_quantity': 0})

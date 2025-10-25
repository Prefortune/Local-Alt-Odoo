from odoo import api, fields, models
import requests
from odoo.exceptions import ValidationError
from itertools import product
import base64
import json

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
        #_logger.info("sync shopify product %s", products)
        existing_products = self.env['product.template'].search([('is_shopify_product', '=', True),('shopify_store', '=', shopify_connector.id),'|',('active', '=', True),('active', '=', False)])
        exclude_ids = []
        for ex_pro in existing_products:
            exclude_ids.append(ex_pro.shopify_product_id)
        # _logger.info("this is all ids exist in odoo %s", exclude_ids)
        self = self.with_context(def_name='sync_product')
        for product in products:
            # if str(product['id']) in exclude_ids and sync_type == "sync_button":
            #     _logger.info("This is match ids %s", product['id'])
            #     continue
            _logger.info("This is product id%s and name %s ", product['id'], product['title'])
            product_id = product['id']
            product_name = product['title']
            product_type = product['product_type']
            product_description = product['body_html']
            active = True if product['status']=='active' else False
            find_exists = product_template.search([('shopify_product_id', '=', product_id),('shopify_store', '=', shopify_connector.id),'|',('active', '=', True),('active', '=', False)])
            _logger.info(len(product['variants']))
            min_price = min(float(variant_price['price']) for variant_price in product['variants'])
            product_dict = {
                'name': product_name,
                'detailed_type': 'product',
                #'list_price': 0 if len(product['variants']) > 1 else product['variants'][0]['price'],
                'list_price': min_price,
                'shopify_product_id': product_id,
                'description': product_description,
                'available_in_pos': True,
                'active':active
            }

            if product['image']:
                image_test = product['images'][0]['src']
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(image_test, headers=headers)
                base64_data = base64.b64encode(response.content).decode('utf-8')
                product_dict['image_1920'] = base64_data

            attribute_line_data = {}

            for attr in product['options']:
                attribute_name = attr['name']
                values = [value.strip() for value in attr['values']]
                
                if attribute_name == "Title":
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

                    product_update = find_exists.write(product_dict)
                else:
                    if attribute_line_ids:
                        product_dict['attribute_line_ids'] = attribute_line_ids
                    product_update = find_exists.write(product_dict)
                
                if product_update:
                    product_template_id = find_exists
            else:
                product_create = product_template.create(product_dict)

                if product_create:
                    product_create.write({'is_shopify_product':True,'shopify_store':shopify_connector})
                    product_template_id = product_create

                    # Archive/Unarchive product variants based on the product template status
                    for variant in product_create.product_variant_ids:
                        variant.write({'active': active})
            #_logger.info("product_dict %s",product_dict)
            # Add shopify_product_id and shopify_product_variant_id to product.product 
            find_exists_variant = product_template.search([('id', '=', product_template_id.id)])
            #_logger.info("len(find_exists_variant['product_variant_ids']) %s",len(find_exists_variant['product_variant_ids']))
            #_logger.info("len(product['variants'] %s",len(product['variants']))
            if len(find_exists_variant['product_variant_ids']) == len(product['variants']):
                self._update_variant_data(find_exists_variant, product, shopify_connector.store_price_list, shopify_connector)
            
                   
    def post_product(self, values, template_id, shopify_store_id):
        shopify_store = self.env['shopify.connector']
        shopify_store_data = shopify_store.search([('id', '=', shopify_store_id)])
        shop_url = shopify_store_data.shopify_url
        store_price_list = shopify_store_data.store_price_list

        product_name =  values['name']
        sales_price = values['list_price']
        product_description = values['description']

        shopify_product_dict = {
            "product": {
                "title": product_name,
                "body_html": product_description,
            }
        }

        if 'image_1920' in values:
            shopify_product_dict['product']['images'] = [
                {
                    "attachment": values['image_1920'],
                    "filename": product_name + ".jpg"  # Change the filename as needed
                }
            ]

        if values['attribute_line_ids']:
            variant_combination = []  # Initialize an empty list to store result variants
            attribute_values_list = []  # Initialize a list to store attribute values
            option_array = []
            for attribute_line in values.get('attribute_line_ids', []):
                atr_val_list = []
                if isinstance(attribute_line[1], str):
                    odoo_attribute_id = attribute_line[2].get('attribute_id')
                    attribute_id = self._get_attribute_details(odoo_attribute_id)
                    value_ids = attribute_line[2].get('value_ids')
                    if value_ids is not None:
                        value_list = value_ids[0][2]
                        attribute_values = [self._get_attribute_value_details(attribute_id, atr_val) for atr_val in value_list]
                        attribute_values_list.append(attribute_values)
                        atr_val_list.extend(attribute_values)
                    option = {
                        'name':attribute_id,
                        'values':atr_val_list,
                    }   
                option_array.append(option)

            # Generate combinations using itertools.product
            combinations = product(*attribute_values_list)

            for combination in combinations:
                variant = {}
                for index, value in enumerate(combination, start=1):
                    variant["option" + str(index)] = value
                    variant["price"] = sales_price
                variant_combination.append(variant)
            # _logger.info("variant dict %s", variant_combination)
            shopify_product_dict["product"]["variants"] = variant_combination
            shopify_product_dict["product"]["options"] = option_array

        response = requests.post(shop_url +"/products.json", json=shopify_product_dict)
        if response.status_code == 201:
            _logger.info("this is new created shopify product %s", response.json())
            shopify_created_product = response.json()["product"]
            template_id.write({'shopify_product_id':shopify_created_product['id']})
            shopify_Variant_length_count = len(shopify_created_product['variants'])
            if shopify_Variant_length_count <= 1:
                single_variant_product_id = shopify_created_product['variants'][0]['id']
                update_price ={
                    "variant":{
                        'price' : sales_price
                    }
                }
                response_update_price = requests.put(shop_url +"/variants/"+ str(single_variant_product_id) + ".json", json=update_price)
                _logger.info("response_update_price %s", response_update_price.json())
            if len(template_id['product_variant_ids']) == len(shopify_created_product['variants']):
                self._update_variant_data(template_id, shopify_created_product, store_price_list, shopify_store_data)          

    def _get_attribute_details(self, attribute_id):
         attribute_data = self.env['product.attribute'].search([('id', '=', attribute_id)])
         return attribute_data.name
    
    def _get_attribute_value_details(self, attribute_id, value_id):
        value_data = self.env['product.attribute.value'].search([('attribute_id', '=', attribute_id),('id', '=', value_id)])
        return value_data.name
    
    def _update_variant_data(self, product_template, shopify_product, store_price_list, shopify_connector):
        product_product = self.env['product.product']
        variant_data = product_product.search([('product_tmpl_id', '=', product_template.id),'|',('active', '=', True),('active', '=', False)])
        if len(variant_data.product_template_attribute_value_ids) > 1:
            _logger.info("_update_variant_data 1")
            for variant in variant_data:
                # Extract attribute names from variant
                variant_names = [rec.name for rec in variant.product_template_attribute_value_ids]
                for shopify_variant in shopify_product['variants']:
                    shopify_title = shopify_variant['title']
                    # Compare variant_names with shopify_title
                    shopify_variant_name = [names.strip() for names in shopify_title.split(' / ')]
                    if all(item in variant_names for item in shopify_variant_name):
                        min_price = float(product_template['list_price'])
                        variant_price = float(shopify_variant['price']) - min_price
                        variant_update_dict = {
                            'shopify_variant_id': shopify_variant['id'],
                            'shopify_product_id': shopify_variant['product_id'],
                            'shopify_store': shopify_connector.id,
                            'active' : True if shopify_product['status']=='active' else False,
                            'custom_price_extra' : variant_price
                        }
                        #_logger.info("variant_price %s id %s",variant_price,shopify_variant['id'])
                        if shopify_variant['image_id']:
                           variant_img_id = shopify_variant['image_id']
                           for product_images in shopify_product['images']:
                               if product_images['id'] == variant_img_id:
                                    #_logger.info("variant id %s and src %s", product_images['variant_ids'], product_images['src'])
                                    # variant_update_dict['image_1920'] = product_images['src']
                                    variant_image_src = product_images['src']
                                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                                    response = requests.get(variant_image_src, headers=headers)
                                    base64_data = base64.b64encode(response.content).decode('utf-8')
                                    variant_update_dict['image_variant_1920'] = base64_data
                        # else:
                        #     _logger.info("this is not image id ")
                        #_logger.info("variant_update_dict %s",variant_update_dict)
                        update_variant = variant.write(variant_update_dict)
                        #_logger.info("update_variant %s",update_variant)
                        #self._update_variant_combination_price(variant, shopify_variant['price'], store_price_list)
        else:
            _logger.info("_update_variant_data 2")
            variant_update_dict = {
                'shopify_variant_id': shopify_product['variants'][0]['id'],
                'shopify_product_id': shopify_product['variants'][0]['product_id'],
                'active' : True if shopify_product['status']=='active' else False
            }
            update_variant = variant_data.write(variant_update_dict)

    def put_product(self, values, template_id, shopify_store_id):
        shop_url = shopify_store_id.shopify_url
        store_price_list = shopify_store_id.store_price_list

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
        if values.get('attribute_line_ids'):
            variant_combination = []  # Initialize an empty list to store result variants
            attribute_values_list = []  # Initialize a list to store attribute values
            option_array = []
            for attribute_line in values.get('attribute_line_ids', []):
                atr_val_list = []
                if attribute_line[0] == 4:
                    attr_line_id = attribute_line[1]
                    attribute_data, value_data  = self._get_attr_id_from_attr_line(template_id, attr_line_id)
                elif attribute_line[0] == 1:
                    attr_line_id = attribute_line[1]
                    attribute_data, value_data  = self._get_attr_id_from_attr_line(template_id, attr_line_id)
                elif attribute_line[0] == 0:
                    attribute_data = attribute_line[2]['attribute_id']
                    value_ids = attribute_line[2].get('value_ids', [])
                    if value_ids:
                        value_data = value_ids[0][2]
                elif attribute_line[0] == 2:
                    continue

                if isinstance(attribute_data, (int, str)):
                    odoo_attribute_id = attribute_data
                    value_list = value_data
                else:
                    odoo_attribute_id = attribute_data.id
                    value_list = [atr_val.id for atr_val in value_data]

                attribute_id = self._get_attribute_details(odoo_attribute_id)
                attribute_values = [self._get_attribute_value_details(odoo_attribute_id, atr_val) for atr_val in value_list]
                attribute_values_list.append(attribute_values)
                atr_val_list.extend(attribute_values)

                option = {
                        'name':attribute_id,
                        'values':atr_val_list
                    }   
                option_array.append(option)

            combinations = product(*attribute_values_list)

            for combination in combinations:
                variant = {}
                for index, value in enumerate(combination, start=1):
                    variant["option" + str(index)] = value
                    variant["price"] = template_id.list_price
                variant_combination.append(variant)
            # _logger.info("variant dict %s", variant_combination)
            shopify_product_dict["product"]["variants"] = variant_combination
            shopify_product_dict["product"]["options"] = option_array
        
        if shopify_product_id is not False:
            response = requests.put(shop_url +"/products/"+ shopify_product_id + ".json", json=shopify_product_dict)
            response_code = 200
        else:
            response = requests.post(shop_url +"/products.json", json=shopify_product_dict)
            response_code = 201

        if response.status_code == response_code:
            shopify_product = response.json()["product"]
            
            template_id.write({'shopify_product_id':shopify_product['id']})
            shopify_Variant_length_count = len(shopify_product['variants'])
            if shopify_Variant_length_count <= 1:
                single_variant_product_id = shopify_product['variants'][0]['id']
                update_price ={
                    "variant":{
                        'price' : template_id.list_price
                    }
                }
                response_update_price = requests.put(shop_url +"/variants/"+ str(single_variant_product_id) + ".json", json=update_price)
                _logger.info("response_update_price %s", response_update_price.json())
            if len(template_id['product_variant_ids']) == len(shopify_product['variants']):
                self._update_variant_data(template_id, shopify_product, store_price_list, shopify_store_id)

    def _get_attr_id_from_attr_line(self, template_id, attr_line_id):
        atr_line_data = self.env['product.template.attribute.line'].search([('id', '=', attr_line_id)])
        return atr_line_data.attribute_id, atr_line_data.value_ids

    def _update_variant_combination_price(self, variant, shopify_product_combination_price, store_price_list):
        #_logger.info("_update_variant_combination_price")
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


from odoo import api, fields, models
import requests
from odoo.exceptions import ValidationError
import logging
from datetime import datetime
_logger = logging.getLogger(__name__)

class ShopifyCoupon(models.Model):
    _name = "shopify.coupon"
    _description = "Shopify Coupon"

    def sync_coupon(self, coupons, shopify_connector, sync_type):
        loyalty_program = self.env['loyalty.program']
        loyalty_reward = self.env['loyalty.reward']
        loyalty_rule = self.env['loyalty.rule']
        for coupon in coupons:
            _logger.info("this is coupon data %s", coupon)
            shopify_coupon_id = coupon['id']
            shopify_code_discount = coupon['codeDiscount']

            if 'customerGets' in shopify_code_discount:
                if shopify_code_discount['customerGets']['items']['__typename'] == "DiscountProducts":
                    if not shopify_code_discount['customerGets']['items']['productVariants']['nodes'] and not shopify_code_discount['customerGets']['items']['products']['nodes']:
                        continue
            
            
            shopify_coupon_name =  coupon['codeDiscount']['title']
            shopify_coupon_start_date = shopify_code_discount['startsAt']
            shopify_coupon_end_date = shopify_code_discount['endsAt']

            if shopify_code_discount['discountClass'] != "SHIPPING":
                shopify_discount_type = shopify_code_discount['customerGets']['value']['__typename']
                # Check Reward Type (% or Amount)
                if shopify_discount_type == "DiscountPercentage":
                    discount_mode = 'percent'
                    shopify_discount_amount = shopify_code_discount['customerGets']['value']['percentage'] * 100
                elif shopify_discount_type == "DiscountAmount":
                    discount_mode = 'per_order'
                    shopify_discount_amount = shopify_code_discount['customerGets']['value']['amount']['amount']
                shopify_discount_amount = abs(float(shopify_discount_amount))


            existing_coupon = loyalty_program.sudo().search([('shopify_coupon_id', '=', shopify_coupon_id),('shopify_store', '=', shopify_connector.id)])
            # Prepare Loyalty Data
            program_data = {
                'name': shopify_coupon_name,
                'active': True,
                'is_shopify_coupon': True,
                'shopify_coupon_id': shopify_coupon_id,
                'shopify_store': shopify_connector.id
            }
            
            # Set Start Time if Require
            if shopify_coupon_start_date is not None:
                date_object = datetime.strptime(shopify_coupon_start_date, '%Y-%m-%dT%H:%M:%S%z')
                shopify_formatted_date = date_object.strftime('%Y-%m-%d %H:%M:%S')
                program_data['date_from'] = shopify_formatted_date

            # Set End Time if Require
            if shopify_coupon_end_date is not None:
                date_object = datetime.strptime(shopify_coupon_end_date, '%Y-%m-%dT%H:%M:%S%z')
                shopify_formatted_date = date_object.strftime('%Y-%m-%d %H:%M:%S')
                program_data['date_to'] = shopify_formatted_date
            

            
            # Select Program type (we use only two: coupons and buy_x_get_y)
            if 'customerBuys' in shopify_code_discount:
                program_type = 'buy_x_get_y'
            else:
                program_type =  'coupons'

                pass
            
            _logger.info("PRogram Type %s", program_type)
            
            # Create Loyalty Program
            if not existing_coupon: 
                program_data['program_type'] = program_type
                loyalty_program_data = loyalty_program.create(program_data)
            else:
                existing_coupon.write(program_data)
                loyalty_program_data = existing_coupon
            
            # Prepare Reward Data 
            if loyalty_program_data:
                if shopify_code_discount['discountClass'] != "SHIPPING":
                    loyalty_reward_data = {
                        'program_id': loyalty_program_data.id,
                        'reward_type': 'discount',
                        'discount': shopify_discount_amount,
                        'discount_mode' : discount_mode,
                    }
                    if shopify_code_discount['discountClass'] == "ORDER":
                        loyalty_reward_data['discount_applicability'] = 'order'
                        add_to_coupon = True
                    elif shopify_code_discount['discountClass'] == "PRODUCT":
                        if 'customerBuys' in shopify_code_discount:
                            if shopify_code_discount['customerBuys']['items']['__typename'] == "DiscountProducts":
                                if shopify_code_discount['customerBuys']['value']['__typename'] == "DiscountQuantity":
                                    require_quantity = shopify_code_discount['customerBuys']['value']['quantity']
                                    
                                    loyalty_rule_data ={
                                        'program_id': loyalty_program_data.id,
                                        'minimum_qty' : require_quantity
                                    }

                                    prerequisite_product_ids = shopify_code_discount['customerBuys']['items']['products']['nodes']
                                    prerequisite_variant_ids = shopify_code_discount['customerBuys']['items']['productVariants']['nodes']
                                    
                                    rule_discount_product_domain_data_list = []
                                    rule_discount_product_domain_list = []

                                    for product_id in prerequisite_product_ids:
                                        discount_product_domain_data = [
                                            ('shopify_qraphql_product_id', 'ilike', str(product_id['id']))
                                        ]
                                        rule_discount_product_domain_data_list.append(discount_product_domain_data)
                                        if len(rule_discount_product_domain_data_list) > 1:
                                            rule_discount_product_domain_list = ["|"] + [item for sublist in rule_discount_product_domain_data_list for item in sublist]
                                        else:
                                            rule_discount_product_domain_list = [item for sublist in rule_discount_product_domain_data_list for item in sublist]
                                    loyalty_rule_data['product_domain'] = rule_discount_product_domain_list

                                    rule_discount_product_variant_ids_data_list = []
                                    for variant_id in prerequisite_variant_ids:
                                        _logger.info("variant_id %s", variant_id['id'])
                                        product_variants = self.env['product.product'].sudo().search([('shopify_qraphql_product_variant_id', '=', variant_id['id']),('shopify_store', '=', shopify_connector.id)])
                                        _logger.info("THis is Product Variant %s", product_variants)
                                        rule_discount_product_variant_ids_data_list.append(product_variants.id)
                                    loyalty_rule_data['product_ids'] = rule_discount_product_variant_ids_data_list

                                    if loyalty_program_data.rule_ids:
                                        _logger.info("This is existing rule id %s", loyalty_program_data.rule_ids)
                                        rule_id = loyalty_program_data.rule_ids
                                        rule_id.write(loyalty_rule_data)
                                        loyalty_rules = rule_id
                                    else:
                                        _logger.info("This is new rule id %s", loyalty_rule_data)
                                        loyalty_rules = loyalty_rule.create(loyalty_rule_data)
                                        _logger.info("This is new rule id create %s",loyalty_rules)

                        if 'customerGets' in shopify_code_discount:
                            product_product = self.env['product.product']

                            loyalty_reward_data['discount_applicability'] = 'specific'
                            product_ids = shopify_code_discount['customerGets']['items']['products']['nodes']
                            variant_ids = shopify_code_discount['customerGets']['items']['productVariants']['nodes']
                            

                            discount_product_domain_data_list = []
                            discount_product_domain_list = []
                            for product_id in product_ids:
                                discount_product_domain_data = [
                                    ('shopify_qraphql_product_id', 'ilike', str(product_id['id']))
                                ]
                                discount_product_domain_data_list.append(discount_product_domain_data)
                                if len(discount_product_domain_data_list) > 1:
                                    discount_product_domain_list = ["|"] + [item for sublist in discount_product_domain_data_list for item in sublist]
                                else:
                                    discount_product_domain_list = [item for sublist in discount_product_domain_data_list for item in sublist]
                            # loyalty_reward_data['discount_product_domain'] = discount_product_domain_list


                            discount_product_variant_ids_data_list = []
                            for variant_id in variant_ids:
                                product_variants = self.env['product.product'].sudo().search([('shopify_qraphql_product_variant_id', '=', variant_id['id']),('shopify_store', '=', shopify_connector.id)])
                                discount_product_variant_ids_data_list.append(product_variants.id)
                            # loyalty_reward_data['discount_product_ids'] = discount_product_variant_ids_data_list

                            if 'customerBuys' in shopify_code_discount and shopify_code_discount['customerBuys']['value']['__typename'] == "DiscountQuantity":
                                    loyalty_reward_data['reward_type'] = 'product'
                                    loyalty_reward_data['reward_product_id'] = discount_product_variant_ids_data_list[0]
                            else:
                                loyalty_reward_data['discount_product_domain'] = discount_product_domain_list
                                loyalty_reward_data['discount_product_ids'] = discount_product_variant_ids_data_list


                else:
                    loyalty_reward_data = {
                            'program_id': loyalty_program_data.id,
                            'reward_type':'shipping'
                        }
            
            # Reward Data
            if loyalty_program_data.reward_ids:
                reward_id = loyalty_program_data.reward_ids
                reward_id.write(loyalty_reward_data)
                loyalty_reward = reward_id
            else:
                loyalty_reward = loyalty_reward.create(loyalty_reward_data)
                
            if loyalty_reward:
                existing_loyalty_reward_description = loyalty_reward.description
                loyalty_reward.write({'description': existing_loyalty_reward_description + " with coupon code " + shopify_coupon_name})
                product_product = self.env['product.product']
                loyalty_reward_product_id = loyalty_reward.discount_line_product_id
                existing_product_id = product_product.sudo().search([('id', '=', loyalty_reward_product_id.id)])
                if existing_product_id:
                    existing_product_id.write({'name': "shopify_coupon " + shopify_coupon_name})

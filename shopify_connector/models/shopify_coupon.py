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
            shopify_discount_type = coupon['value_type']
            shopify_discount_amount = coupon['value']
            shopify_discount_amount = abs(float(shopify_discount_amount))
            shopify_coupon_name =  coupon['title']
            shopify_coupon_end_date = coupon['ends_at']

            if shopify_discount_type == "percentage":
                discount_mode = 'percent'
            elif shopify_discount_type == "fixed_amount":
                discount_mode = 'per_order'

            existing_coupon = loyalty_program.sudo().search([('shopify_coupon_id', '=', shopify_coupon_id),('shopify_store', '=', shopify_connector.id)])
            # Prepare Loyalty Data
            program_data = {
                'name': shopify_coupon_name,
                'active': True,
                # 'program_type': 'coupons',
                'is_shopify_coupon': True,
                'shopify_coupon_id': shopify_coupon_id,
                'shopify_store': shopify_connector.id
            }

            # Set End Time if Require
            if shopify_coupon_end_date is not None:
                date_object = datetime.strptime(shopify_coupon_end_date, '%Y-%m-%dT%H:%M:%S%z')
                shopify_formatted_date = date_object.strftime('%Y-%m-%d %H:%M:%S')
                program_data['date_to'] = shopify_formatted_date
            
            # Select Program type (we use only two: coupons and buy_x_get_y)
            if not coupon['prerequisite_product_ids'] and not coupon['prerequisite_variant_ids'] and not coupon['prerequisite_collection_ids']:
                program_type = 'coupons'
            else:
                program_type = 'buy_x_get_y'
            
            # Create Loyalty Program
            if not existing_coupon: 
                program_data['program_type'] = program_type
                loyalty_program_data = loyalty_program.create(program_data)
            else:
                existing_coupon.write(program_data)
                loyalty_program_data = existing_coupon
            
            # Prepare Reward Data 
            if loyalty_program_data:
                if coupon['target_type'] == "line_item":
                    loyalty_reward_data = {
                        'program_id': loyalty_program_data.id,
                        'reward_type': 'discount',
                        'discount': shopify_discount_amount,
                        'discount_mode' : discount_mode,
                    }
                    if coupon['target_selection'] == "all":
                        loyalty_reward_data['discount_applicability'] = 'order'
                        add_to_coupon = True
                    elif coupon['target_selection'] == "entitled":
                        if coupon['prerequisite_product_ids'] or coupon['prerequisite_variant_ids']:
                            prerequisite_quantity = coupon['prerequisite_to_entitlement_quantity_ratio']['prerequisite_quantity']
                            
                            loyalty_rule_data ={
                                'program_id': loyalty_program_data.id,
                                'minimum_qty' : prerequisite_quantity
                            }

                            prerequisite_product_ids = coupon['prerequisite_product_ids']
                            prerequisite_variant_ids = coupon['prerequisite_variant_ids']
                            
                            rule_discount_product_domain_data_list = []
                            rule_discount_product_domain_list = []
                            for product_id in prerequisite_product_ids:
                                discount_product_domain_data = [
                                    ('shopify_product_id', 'ilike', str(product_id))
                                ]
                                rule_discount_product_domain_data_list.append(discount_product_domain_data)
                                if len(rule_discount_product_domain_data_list) > 1:
                                    rule_discount_product_domain_list = ["|"] + [item for sublist in rule_discount_product_domain_data_list for item in sublist]
                                else:
                                    rule_discount_product_domain_list = [item for sublist in rule_discount_product_domain_data_list for item in sublist]
                            loyalty_rule_data['product_domain'] = rule_discount_product_domain_list

                            rule_discount_product_variant_ids_data_list = []
                            for variant_id in prerequisite_variant_ids:
                                product_variants = self.env['product.product'].sudo().search([('shopify_variant_id', '=', variant_id),('shopify_store', '=', shopify_connector.id)])
                                rule_discount_product_variant_ids_data_list.append(product_variants.id)
                            loyalty_rule_data['product_ids'] = rule_discount_product_variant_ids_data_list

                            if loyalty_program_data.rule_ids:
                                _logger.info("This is existing rule id %s", loyalty_program_data.rule_ids)
                                rule_id = loyalty_program_data.rule_ids
                                rule_id.write(loyalty_rule_data)
                                loyalty_rules = rule_id
                            else:
                                _logger.info("This is new rule id")
                                loyalty_rules = loyalty_rule.create(loyalty_rule_data)
                                _logger.info("This is new rule id create %s",loyalty_rules)

                        if coupon['entitled_product_ids'] or coupon['entitled_variant_ids']:
                            product_product = self.env['product.product']
                            loyalty_reward_data['discount_applicability'] = 'specific'
                            product_ids = coupon['entitled_product_ids']
                            variant_ids = coupon['entitled_variant_ids']
                            

                            discount_product_domain_data_list = []
                            discount_product_domain_list = []
                            for product_id in product_ids:
                                discount_product_domain_data = [
                                    ('shopify_product_id', 'ilike', str(product_id))
                                ]
                                discount_product_domain_data_list.append(discount_product_domain_data)
                                if len(discount_product_domain_data_list) > 1:
                                    discount_product_domain_list = ["|"] + [item for sublist in discount_product_domain_data_list for item in sublist]
                                else:
                                    discount_product_domain_list = [item for sublist in discount_product_domain_data_list for item in sublist]
                            loyalty_reward_data['discount_product_domain'] = discount_product_domain_list


                            discount_product_variant_ids_data_list = []
                            for variant_id in variant_ids:
                                product_variants = self.env['product.product'].sudo().search([('shopify_variant_id', '=', variant_id),('shopify_store', '=', shopify_connector.id)])
                                discount_product_variant_ids_data_list.append(product_variants.id)
                            loyalty_reward_data['discount_product_ids'] = discount_product_variant_ids_data_list

                elif coupon['target_type'] == "shipping_line":
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

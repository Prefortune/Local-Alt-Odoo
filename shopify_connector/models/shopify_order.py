from odoo import api, fields, models ,_
import requests
from dateutil import parser

from odoo.exceptions import ValidationError
import json
import datetime
import pytz  # To handle timezone conversions

import logging
_logger = logging.getLogger(__name__)

class ShopifyOrder(models.Model):
    _name = "shopify.order"
    _description = "Shopify Order"

    def _create_product_if_variant_not_found(self, shopify_product_id, product_name, product_price, shopify_store):
        product_product = self.env['product.product']
        if shopify_product_id:
            check_archive_product_template = product_product.sudo().search([('name', '=', product_name),('shopify_product_id', '=', shopify_product_id),('shopify_store', '=', shopify_store.id),('active', '=', False)])
            if not check_archive_product_template:
                create_dict = {
                    'name':product_name,
                    'list_price': product_price,
                }
                delete_woo_product_variant_in_odoo = product_product.sudo().create(create_dict)
                delete_woo_product_variant_in_odoo.sudo().write({'shopify_product_id':shopify_product_id,'shopify_variant_id':shopify_product_id,'shopify_store':shopify_store.id,'active':False})
                delete_woo_product_id = delete_woo_product_variant_in_odoo.product_tmpl_id
                delete_woo_product_id.sudo().write({'shopify_product_id':shopify_product_id,'shopify_store':shopify_store.id,'active':False})
                return delete_woo_product_variant_in_odoo
            else:
                return check_archive_product_template
        else:
            check_archive_product_template = product_product.sudo().search([('name', '=', product_name),('shopify_store', '=', shopify_store.id),('active', '=', False)])
            if not check_archive_product_template:
                create_dict = {
                    'name':product_name,
                    'list_price': product_price,
                    'shopify_store':shopify_store.id
                }
                delete_woo_product_variant_in_odoo = product_product.sudo().create(create_dict)
                return delete_woo_product_variant_in_odoo
            else:
                return check_archive_product_template


    def sync_order(self, orders, shop_url, shopify_connector, sync_type):
        sale_order = self.env['sale.order']
        invoice_model = self.env['sale.advance.payment.inv']
        existing_orders = sale_order.search([('is_shopify_order', '=', True),('shopify_store', '=', shopify_connector.id)])
        sale_order_tag = self.get_order_tag('Shopify')
        exclude_ids = []
        for ex_pro in existing_orders:
            exclude_ids.append(ex_pro.shopify_order_id)
        for order in orders:
            # if str(order['id']) in exclude_ids and sync_type == "sync_button":
            #     continue
            if order.get('customer') and order['customer'].get('id'):
                shopify_customer_id = order['customer']['id']
                shopify_order_id = order['id']
                _logger.info("shopify_order_id %s",shopify_order_id)
                partner_data = self.env['res.partner'].search([('shopify_customer_id', '=', shopify_customer_id),('parent_id', '=', False), ('shopify_store', '=', shopify_connector.id)])
                
                if not partner_data:
                    response = requests.get(shop_url + "/customers/"+ str(shopify_customer_id) +".json")
                    customers = response.json()["customer"]
                    customers = [customers]
                    shopify_customer = self.env['shopify.customer']
                    shopify_customer.sync_customer(customers, shopify_connector, sync_type)
                    partner_data = self.env['res.partner'].search([('shopify_customer_id', '=', shopify_customer_id),('parent_id', '=', False), ('shopify_store', '=', shopify_connector.id)])
                
                order_billing_address, order_shipping_address = self._shopify_address(order, shopify_customer_id, partner_data)

                existing_order = self.env['sale.order'].search([('shopify_order_id', '=', shopify_order_id),('partner_id', '=', partner_data.id), ('shopify_store', '=', shopify_connector.id)])

                date = order.get('created_at')
                _logger.info("date -------- %s",date)
                try:
                    shopify_time = parser.parse(date)
                
                    if shopify_time.tzinfo is not None:
                        utc_time = shopify_time.astimezone(pytz.utc)
                    else:
                        utc_time = shopify_time

                    formatted_date = utc_time.strftime('%Y-%m-%d %H:%M:%S')
                    _logger.info("Formatted UTC date for Odoo: %s", formatted_date)
                except ValueError as e:
                    _logger.error("Date parsing error: %s", e)
                    raise ValidationError(_('Invalid date format from Shopify: %s' % date))
                
                if not existing_order:
                    order_data = {
                        'shopify_order_id': shopify_order_id,
                        'shopify_store': shopify_connector.id,
                        'is_shopify_order': True,
                        'partner_id': partner_data.id,
                        'state': 'sale',
                        'order_line': [],
                        'pricelist_id': shopify_connector.store_price_list.id,
                        'partner_invoice_id': order_billing_address.id,
                        'partner_shipping_id': order_shipping_address.id,
                        'date_order' : formatted_date,
                        'sale_order_tag' : sale_order_tag
                    }
                    order_id = self.env['sale.order'].create(order_data)
                    existing_order = order_id

                update_in_order = False 
                order_lines = []
                product_dict=[]
                for order_product in order['line_items']:
                    #if order_product['product_exists']:
                    shopify_order_line_id = order_product['id']
                    if not order_product['product_exists']:
                        product_data = self._create_product_if_variant_not_found(False, order_product['name'], order_product['price'], shopify_connector)
                    else:
                        product_id = order_product['product_id']
                        product_variant_id = order_product['variant_id']
                        product_data = self.env['product.product'].search([('shopify_product_id', '=', product_id),('shopify_variant_id', '=', product_variant_id)])
                        if not product_data:
                            _logger.info("THis is not product found in existing %s and var is %s",product_id, product_variant_id)
                            response = requests.get(shop_url + "/products/"+ str(product_id) +".json")
                            products = response.json()["product"]
                            products = [products]
                            shopify_product = self.env['shopify.product']
                            shopify_product.sync_product(products, shopify_connector, sync_type)
                            product_data = self.env['product.product'].search([('shopify_product_id', '=', product_id),('shopify_variant_id', '=', product_variant_id)])
                            if not product_data:
                                product_data = self._create_product_if_variant_not_found(product_id, order_product['name'], order_product['price'], shopify_connector)
                                _logger.info("THis is else of order line ids  variant id %s ", product_data )
                            _logger.info("this is new created product %s", product_data)
                    

                    existing_order_line = self.env['sale.order.line'].search([('order_id', '=', existing_order.id),('shopify_order_line_id', '=', shopify_order_line_id),('product_id', '=', product_data.id)])
                    if existing_order_line:
                        if not existing_order_line.product_uom_qty == order_product['current_quantity']:
                            existing_order_line.write({
                                'product_uom_qty': order_product['current_quantity'],
                            })
                            update_in_order = True
                    else:
                        if order_product['current_quantity'] >= 1:
                            tax_id = False
                            if 'tax_lines' in order_product and order_product['tax_lines']:
                                rate = order_product['tax_lines'][0]['rate']
                                tax_percentage = rate * 100
                                tax_domain = [('amount', '=', tax_percentage), ('type_tax_use', '=', 'sale')]
                                taxes_included = order['taxes_included']
                                if taxes_included:
                                    tax_included = True
                                    tax_domain.append(('price_include', '=', tax_included))
                                    tax_name = 'Sales Tax '+str(tax_percentage)+'% (include)'
                                else:
                                    tax_included = False
                                    tax_domain.append(('price_include', '=', tax_included))
                                    tax_name = 'Sales Tax '+str(tax_percentage)+'%'
                                tax = self.env['account.tax'].search(tax_domain, limit=1)
                                if tax['id']:
                                    tax_id = [(6, 0, [tax['id']])]
                                else:
                                    tax = self.env['account.tax'].create({
                                        'name': tax_name,
                                        'amount': tax_percentage,
                                        'type_tax_use': 'sale',
                                        'price_include': tax_included,
                                        'amount_type': 'percent',  # Assuming percentage-based tax
                                    })
                                    tax_id = [(6, 0, [tax['id']])]
                            
                            # if order['discount_codes']:
                            #     discount_codes = order['discount_codes']
                            #     custom_discount = next((discount for discount in discount_codes if discount['code'] == "Custom discount"), None)
                            #     if custom_discount:
                            #         discount_amount = custom_discount['amount']
                            #         discount_type = custom_discount['type']
                            #         if discount_type=='fixed_amount':
                            #             dis_perc = (discount_amount*100)/order_product['price']


                            product_dict = (0, 0, {
                                'product_id': product_data.id,
                                'shopify_order_line_id':shopify_order_line_id,
                                'price_unit':order_product['price'],
                                'tax_id':tax_id,
                                'product_uom_qty': order_product['current_quantity'],
                            })
                            _logger.info("product_dict %s",product_dict)
                            order_lines.append(product_dict)
                            update_in_order = True
                order_notes = order['note']          
                existing_order.write({'order_line': order_lines,'partner_shipping_id':order_shipping_address.id,'partner_invoice_id': order_billing_address.id,'order_notes':order_notes})


                for item_line in order['line_items']:
                    if item_line['total_discount'] != "0.00":
                        sale_line = self.env['sale.order.line'].search([('order_id', '=', existing_order.id),('shopify_order_line_id', '=', item_line['id'])])
                        product_price = sale_line.price_unit * item_line['current_quantity']
                        discount_percentage = (float(item_line['total_discount'])/float(product_price)) * 100
                        if not round(sale_line.discount, 2) == round(discount_percentage, 2):
                            _logger.info("This is mismatch of odoo and shopify discount %s", item_line['total_discount'])
                            sale_line.write({'discount':discount_percentage,'discount_amount':item_line['total_discount']})
                            update_in_order = True
                # applying coupen code      
                if order['discount_codes']:
                    loyalty_program = self.env['loyalty.program']
                    loyalty_card = self.env['loyalty.card']
                    if not existing_order['applied_coupon_ids']:
                        all_discount_codes = {code['code'] for code in order['discount_codes']}
                        for discount in order['discount_applications']:
                            if discount.get('code'):
                                code = discount.get('code')
                                if code and code in all_discount_codes:
                                    coupon_data = self.fetch_and_sync_coupon(discount, shopify_connector, shop_url, sync_type)  
                                    # Create Coupon
                                    if coupon_data:
                                        if coupon_data.program_type != "buy_x_get_y":
                                            _logger.info("THis is is coupon data %s", coupon_data)
                                            self._apply_coupon_on_order(coupon_data, existing_order)
                                        else:
                                            _logger.info("This is BXGY Coupon Type %s", coupon_data)
                                            self._apply_BXGY_on_order(coupon_data, existing_order)
                
                # applying custom discount
                if order['discount_codes']:
                    for discount in order['discount_applications']:
                        if 'code' not in discount and discount['allocation_method']=='across' and discount['target_selection']=='all':
                            if discount['value_type']=='percentage':
                                discount_description = _("Discount: %(percent)s%%", percent=discount.get('value'))
                                sale_line = self.env['sale.order.line'].search([('order_id', '=', existing_order.id),('name', '=', discount_description)])
                                if sale_line:
                                    continue
                                discount_percentage = float(discount.get('value'))/100
                                obj = {'sale_order_id': existing_order.id,'discount_type':'so_discount','discount_percentage':discount_percentage}
                                _logger.info("discount_description %s",discount_description)
                                _logger.info("sale_line %s",sale_line)
                            else:
                                sale_line = self.env['sale.order.line'].search([('order_id', '=', existing_order.id),('name', '=', 'Discount')])
                                if sale_line['id']:
                                    continue
                                discount_amount = discount.get('value')
                                obj = {'sale_order_id': existing_order.id,'discount_type':'amount','discount_amount':discount_amount}
                            _logger.info("obj %s",obj)
                            wizard = self.env['sale.order.discount'].create(obj).action_apply_discount()
                
                if update_in_order:
                    _logger.info("This is update_in_order invoice ids %s", existing_order.invoice_ids)
                    invoice_id = existing_order.invoice_ids
                    if invoice_id.state == "posted":
                        payments_widget = invoice_id.invoice_payments_widget
                        if isinstance(payments_widget, str):
                            payments_widget = json.loads(payments_widget)
                        if payments_widget and 'content' in payments_widget and payments_widget['content']:
                            move_id = payments_widget['content'][0].get('move_id')
                            if move_id:
                                move_id = self.env['account.move'].search([('id', '=', move_id)])
                                _logger.info("move_id is %s", move_id)
                                move_id.button_draft()
                                move_id.remove_invoice()
                        invoice_id.button_draft()
                        invoice_id.remove_invoice()

                if order['financial_status'] == "paid" and product_dict:
                    account_move = existing_order.invoice_ids
                    if existing_order.state == 'sale' and not account_move:
                        invoice_vals, account_move  = self.create_shopify_order_invoice(existing_order)
                        
                    if existing_order.state == 'sale' and account_move and account_move.state != "posted":
                        invoice_post = self.shopify_order_invoice_post_entry(account_move)
                     
                    if existing_order.state == 'sale' and account_move and account_move.state == "posted" and account_move.payment_state != "paid":       
                        confirm_payment = self.register_shopify_order_payment(account_move)

                    if existing_order.state == 'sale' and account_move and account_move.state == "posted" and account_move.payment_state == "paid":
                        if account_move.invoice_payments_widget and account_move.invoice_payments_widget.get('content'):
                            if len(account_move.invoice_payments_widget['content']) > 0:
                                _logger.info("this is account move id %s", account_move.invoice_payments_widget['content'][0]['account_payment_id'])
                                account_payment_id = account_move.invoice_payments_widget['content'][0]['account_payment_id']
                                if account_payment_id:
                                    invoice_date = account_move.invoice_date
                                    _logger.info("invoice ------ date ---- %s",invoice_date)
                                    account_payment = self.env['account.payment'].search([('id', '=', account_payment_id)])
                                    account_payment.write({'date':invoice_date})
                            else:
                                _logger.info("No payment content available for this account move.")
                        else:
                            _logger.info("No payment widget data found for this account move.")
            else:
                _logger.info("THis is else of customer id")

    def create_shopify_order_invoice(self, order_id):
        invoices = order_id._create_invoices()
        invoices.write({
            'invoice_date': order_id.date_order,
            'invoice_date_due' : order_id.date_order
        })
        return invoices, order_id.invoice_ids
    
    def shopify_order_invoice_post_entry(self, order_id):
        order_post_entry = order_id.action_post()
        return order_post_entry
    
    def register_shopify_order_payment(self, order_id):
        payment = order_id.action_register_payment()
        _logger.info("acount . mobe id ---------- %s",order_id)
        _logger.info("payment id ------------ %s",payment)
    
        payment_id = payment['context']['active_ids']
        _logger.info("payment id -------------- %s",payment_id)
        if payment_id:
            payment_register = self.env['account.payment.register'].browse(payment_id)
            _logger.info("payment register -------------- %s",payment_register)

            invoice_date = order_id.invoice_date
            if not invoice_date:
                invoice_date = fields.Date.today()
            
            _logger.info("Invoice Date -------------- %s", invoice_date)

            create_payment_register = payment_register.with_context({'active_model': 'account.move', 'active_ids': [order_id.id]}).create({}).action_create_payments()
            _logger.info("create payment register -------------- %s",payment_register)
            return create_payment_register
        
    def _shopify_address(self, order, shopify_customer_id, partner_data):
        _logger.info("THis is _shopify_address")
        res_partner = self.env['res.partner']
        if order.get('billing_address'):
            # if order['billing_address']:
            billing_address = order['billing_address']                
            address1 = billing_address['address1'] if billing_address['address1'] != "" and billing_address['address1'] is not None else False
            address2 = billing_address['address2'] if billing_address['address2'] != "" and billing_address['address2'] is not None else False
            partner_billing = self.env['res.partner'].search([('shopify_customer_id', '=', shopify_customer_id),('street', '=', address1),('street2', '=', address2)], limit=1)
            if partner_billing:
                partner_billing_address = partner_billing
            else:
                customer_new_billing_address = self._create_address_dict(shopify_customer_id, billing_address, 'invoice', partner_data.id)
                new_res_partner_billing = res_partner.create(customer_new_billing_address)
                partner_billing_address = new_res_partner_billing
            order_billing_address = partner_billing_address
        else:
            order_billing_address = partner_data
            _logger.info("This is null billing address")
        if order.get('shipping_address'):
            # if order['shipping_address']:
            shipping_address = order['shipping_address']
            address1 = shipping_address['address1'] if shipping_address['address1'] != "" and shipping_address['address1'] is not None else False
            address2 = shipping_address['address2'] if shipping_address['address2'] != "" and shipping_address['address2'] is not None else False
            partner_shipping = res_partner.search([('shopify_customer_id', '=', shopify_customer_id),('street', '=', address1), ('street2', '=', address2)], limit=1)
            if partner_shipping:
                partner_shipping_address = partner_shipping
            else:
                customer_new_shipping_address = self._create_address_dict(shopify_customer_id, shipping_address, 'delivery', partner_data.id)
                new_res_partner_billing = res_partner.create(customer_new_shipping_address)
                partner_shipping_address = new_res_partner_billing
            order_shipping_address = partner_shipping_address
        else:
            order_shipping_address = partner_data
            _logger.info("This is null Shipping address")
        _logger.info("THis is billing address %s and shipping address %s", order_billing_address, order_shipping_address)
        return order_billing_address, order_shipping_address
    
    def _create_address_dict(self, customer_id, address, address_type, parent_id=None):
        address_street = address.get('address1')
        address_street2 = address.get('address2')
        name = address.get('name')
        city = address.get('city')
        postcode = address.get('postcode')
        state = address.get('state')
        country = address.get('country')

        street = address_street if address_street != "" and address_street is not None else False
        street2 = address_street2 if address_street2 != "" and address_street2 is not None else False

        country_id, state_id = self._get_country_and_state_ids(country, state)

        return {
            'shopify_customer_id': customer_id,
            'parent_id': parent_id,
            'name': name,
            'type': address_type,
            'street': street,
            'street2': street2,
            'city': city,
            'state_id': state_id,
            'zip': postcode,
            'country_id': country_id,
        }
    
    def _get_country_and_state_ids(self, country_name, state_name):
        country_id, state_id = False, False

        if country_name:
            country = self.env['res.country'].search([('code', '=', country_name)])
            if country:
                country_id = country.id

        if state_name:
            state = self.env['res.country.state'].search([('code', '=', state_name),('country_id', '=', country_id)])
            if state:
                state_id = state.id

        return country_id, state_id
    
    def fetch_and_sync_coupon(self, discount, shopify_connector, shop_url, sync_type):
        coupon_program = self.env['loyalty.program']
        discount_code = discount['code']
        coupon_data = coupon_program.sudo().search([('name', '=', discount_code),('shopify_store', '=', shopify_connector.id)])
        if coupon_data:
            shopify_coupon = coupon_data.shopify_coupon_id
            response = requests.get(shop_url + "/price_rules/"+ shopify_coupon +".json")
            coupons = response.json()["price_rule"]
            if coupons:
                shopify_coupon = self.env['shopify.coupon']
                shopify_coupon.sync_coupon([coupons], shopify_connector, sync_type)
        else:
            response = requests.get(shop_url + "/price_rules.json")
            coupons = response.json()["price_rules"]
            for coupon in coupons:
                if discount_code == coupon['title']:
                    _logger.info("found matching coupon %s", discount_code)
                    shopify_coupon = self.env['shopify.coupon']
                    shopify_coupon.sync_coupon([coupon], shopify_connector, sync_type)
                
            coupon_data = coupon_program.sudo().search([('name', '=', discount_code),('shopify_store', '=', shopify_connector.id)])
        _logger.info("This is fetch and sync coupon %s and reward id is %s", coupon_data, coupon_data.reward_ids)
        return coupon_data
    
    def check_discount_type(self, discounts):
        for discount in discounts:
            if discount['type'] == 'manual':
                return True
        return False
    
    def _apply_coupon_on_order(self, coupon_data, existing_order):
        loyalty_card = self.env['loyalty.card']
        reward = self.env['loyalty.reward'].sudo().browse(coupon_data.reward_ids.id)
        _logger.info("Reward data id is %s", reward)

        # Create a coupon with the given loyalty program and points
        coupon_vals = {'program_id': coupon_data.id, 'points': 1}
        coupon_ids = loyalty_card.sudo().create(coupon_vals)
        _logger.info("Created coupon id %s", coupon_ids)
        coupon_code = coupon_ids.code
        _logger.info("Created code %s", coupon_code)
        
        # Apply the coupon to the order
        apply_coupon = existing_order._apply_program_reward(reward, coupon_ids)
        existing_order.write({'applied_coupon_ids':coupon_ids})

    def _apply_BXGY_on_order(self, coupon_data, existing_order):
        wizard = self.env['sale.loyalty.reward.wizard'].create({'order_id': existing_order.id,'selected_reward_id':coupon_data.reward_ids.id})
        coupon_vals = {'program_id': coupon_data.id, 'points': 2}
        coupon_ids = self.env['loyalty.card'].sudo().create(coupon_vals)
        existing_order.write({'applied_coupon_ids':coupon_ids})
        wizard.action_apply()
    
    def get_order_tag(self,tag_name):
        tag = self.env['pf.order.tag'].search([('name', '=', tag_name)], limit=1)
        if tag['id']:
            tag_id = tag['id']
        else:
            tag = self.env['pf.order.tag'].create({
                'name': tag_name
            })
            tag_id = tag['id']
        return tag_id
from odoo import api, fields, models
import requests
from odoo.exceptions import ValidationError
import json
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime


class ShopifyOrder(models.Model):
    _name = "shopify.order"
    _description = "Shopify Order"

    def sync_order(self, orders, shop_url, shopify_connector, sync_type):
        sale_order = self.env['sale.order']
        invoice_model = self.env['sale.advance.payment.inv']
        existing_orders = sale_order.search([('is_shopify_order', '=', True),('shopify_store', '=', shopify_connector.id)])
        exclude_ids = []
        # for ex_pro in existing_orders:
        #     exclude_ids.append(ex_pro.shopify_order_id)
        for order in orders:
            # if str(order['id']) in exclude_ids and sync_type == "sync_button":
            #     continue
            if order.get('customer') and order['customer'].get('id'):
                shopify_customer_id = order['customer']['id']
                shopify_order_id = order['id']
                date_order = order['createdAt']
                date_order = datetime.strptime(date_order, "%Y-%m-%dT%H:%M:%SZ")
                date_order = fields.Datetime.to_string(date_order)
                partner_data = self.env['res.partner'].search([('shopify_customer_id', '=', shopify_customer_id),('parent_id', '=', False), ('shopify_store', '=', shopify_connector.id)])
            
                if not partner_data:
                    _logger.info("Customer Not Found")
                    _logger.info("shopify_customer_id %s",shopify_customer_id)
                #     response = requests.get(shop_url + "/customers/"+ str(shopify_customer_id) +".json")
                #     customers = response.json()["customer"]
                #     customers = [customers]
                #     shopify_customer = self.env['shopify.customer']
                #     shopify_customer.sync_customer(customers, shopify_connector, sync_type)
                #     partner_data = self.env['res.partner'].search([('shopify_customer_id', '=', shopify_customer_id),('parent_id', '=', False), ('shopify_store', '=', shopify_connector.id)])
                    
                    shopify_connector.import_shopify_customer_by_id(shopify_customer_id)
                    partner_data = self.env['res.partner'].search([('shopify_customer_id', '=', shopify_customer_id),('parent_id', '=', False), ('shopify_store', '=', shopify_connector.id)])


                order_billing_address, order_shipping_address = self._shopify_address(order, shopify_customer_id, partner_data)
                existing_order = self.env['sale.order'].search([('shopify_order_id', '=', shopify_order_id),('partner_id', '=', partner_data.id), ('shopify_store', '=', shopify_connector.id)])

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
                        'tag_ids' : shopify_connector.tag_ids,
                    }
                    if shopify_connector.force_accounting_date:
                        order_data.update({'date_order': date_order})
                    if shopify_connector.sale_journal:
                        order_data.update({'journal_id': shopify_connector.sale_journal.id})
                    _logger.info("This is new order %s", order_data)
                    order_id = self.env['sale.order'].create(order_data)
                    existing_order = order_id

                update_in_order = False 
                order_lines = []
                for order_product in order['lineItems']['nodes']:
                    variant_archived_product = False
                    if not order_product.get('variant'):
                        product_variant_archived = self._fetch_product_by_name(order_product, shopify_connector)
                        variant_archived_product = True


                    if (order_product.get('variant') and order_product['variant']['product']['status'] in ["ACTIVE","DRAFT","ARCHIVED"]) or variant_archived_product:
                        shopify_order_line_id = order_product['id']
                        product_variant_price = order_product['discountedUnitPrice']
                        if not variant_archived_product:
                            product_id = order_product['variant']['product']['id']
                            product_variant_id = order_product['variant']['id']
                            

                            product_data = self.env['product.product'].search([('shopify_qraphql_product_id', '=', product_id),('shopify_qraphql_product_variant_id', '=', product_variant_id)])
                            if not product_data:
                                _logger.info("THis is not product found in existing %s and var is %s",product_id, product_variant_id)
                                # response = requests.get(shop_url + "/products/"+ str(product_id) +".json")
                                # products = response.json()["product"]
                                # products = [products]
                                # shopify_product = self.env['shopify.product']
                                # shopify_product.sync_product(products, shopify_connector, sync_type)
                                # product_data = self.env['product.product'].search([('shopify_product_id', '=', product_id),('shopify_variant_id', '=', product_variant_id)])
                                # _logger.info("this is new created product %s", product_data)
                                shopify_connector.import_shopify_product_by_id(product_id)
                                product_data = self.env['product.product'].search([('shopify_qraphql_product_id', '=', product_id),('shopify_qraphql_product_variant_id', '=', product_variant_id)])
                        else:
                            product_data = product_variant_archived

                        existing_order_line = self.env['sale.order.line'].search([('order_id', '=', existing_order.id),('shopify_order_line_id', '=', shopify_order_line_id),('product_id', '=', product_data.id)])
                        if existing_order_line:
                            if not existing_order_line.product_uom_qty == order_product['currentQuantity']:
                                existing_order_line.write({
                                    'product_uom_qty': order_product['currentQuantity'],
                                })
                                update_in_order = True
                        else:
                            if order_product['currentQuantity'] >= 1:

                                tax_id = False
                                if 'taxLines' in order_product and order_product['taxLines']:
                                    tax_percentage = order_product['taxLines'][0]['ratePercentage']
                                    tax_title = order_product['taxLines'][0]['title']
                                    tax_domain = [('amount', '=', tax_percentage), ('type_tax_use', '=', 'sale')]
                                    taxes_included = order['taxesIncluded']
                                    if taxes_included:
                                        tax_included = True
                                        tax_domain.append(('price_include', '=', tax_included))
                                        tax_name = f'{str(tax_percentage)} % {tax_title} (include)'
                                    else:
                                        tax_included = False
                                        tax_domain.append(('price_include', '=', tax_included))
                                        tax_name = f'{str(tax_percentage)} % {tax_title}'
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

                                product_dict = (0, 0, {
                                    'product_id': product_data.id,
                                    'shopify_order_line_id':shopify_order_line_id,
                                    'price_unit':product_variant_price,
                                    'tax_id':tax_id,
                                    'product_uom_qty': order_product['currentQuantity'],
                                })
                                order_lines.append(product_dict)
                                update_in_order = True

                # if not order_lines:
                #     continue       
                # existing_order.write({'order_line': order_lines,'partner_shipping_id':order_shipping_address.id,'partner_invoice_id': order_billing_address.id})

                if order_lines:
                    existing_order.write({'order_line': order_lines,'partner_shipping_id':order_shipping_address.id,'partner_invoice_id': order_billing_address.id})

                if order.get("fulfillments",False):
                    delivery_status = order["fulfillments"][0].get("displayStatus", False)
                    if delivery_status == 'DELIVERED':
                        done_picking = existing_order.picking_ids.filtered(lambda p: p.state == "done")
                        if not done_picking:
                            _logger.info("Craete delivered status for order %s", existing_order)
                            existing_order.create_manufacture_order()
                            existing_order.ordered_delivered()

                if order['discountCode']:
                    loyalty_program = self.env['loyalty.program']
                    loyalty_card = self.env['loyalty.card']
                    if not existing_order['applied_coupon_ids']:
                        all_discount_codes = {code for code in order['discountCodes']}
                        for discount in order['discountApplications']['nodes']:
                            if discount.get('code'):
                                code = discount.get('code')
                                if code and code in all_discount_codes:
                                    _logger.info("COde in All code %s", code)
                                    coupon_data = self.fetch_and_sync_coupon(discount, shopify_connector, shop_url, sync_type)  
                                    # Create Coupon
                                    if coupon_data:
                                        if coupon_data.program_type != "buy_x_get_y":
                                            simple_coupon_apply = self._apply_coupon_on_order(coupon_data, existing_order)
                                            _logger.info("simple_coupon_apply %s", simple_coupon_apply)
                                        else:
                                            bxgy_apply = self._apply_BXGY_on_order(coupon_data, existing_order)
                                            _logger.info("bxgy_apply %s", bxgy_apply)

                # for item_line in order['lineItems']['nodes']:
                #     if item_line['totalDiscount'] != "0.00":
                #         sale_line = self.env['sale.order.line'].search([('order_id', '=', existing_order.id),('shopify_order_line_id', '=', item_line['id'])])
                #         product_price = sale_line.price_unit * item_line['currentQuantity']
                #         discount_percentage = (float(item_line['totalDiscount'])/float(product_price)) * 100
                #         if not round(sale_line.discount, 2) == round(discount_percentage, 2):
                #             _logger.info("This is mismatch of odoo and shopify discount %s", item_line['totalDiscount'])
                #             sale_line.write({'discount':discount_percentage,'discount_amount':item_line['totalDiscount']})
                #             update_in_order = True
                
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

                if order['displayFinancialStatus'] == "PAID":
                    _logger.info("THis is existing_order %s", existing_order.name)
                    account_move = existing_order.invoice_ids
                    if existing_order.state == 'sale' and not account_move:
                        invoice_vals, account_move  = self.create_shopify_order_invoice(existing_order,shopify_connector.force_accounting_date)
                        _logger.info("invoice_vals %s & account_move %s", invoice_vals, account_move)
                        
                    if existing_order.state == 'sale' and account_move and account_move.state != "posted":
                        _logger.info("Posted %s", account_move)
                        _logger.info("Posted State %s", account_move.state)
                        invoice_post = self.shopify_order_invoice_post_entry(account_move)
                        _logger.info("THis is invoice_post %s", invoice_post)
    
                    if existing_order.state == 'sale' and account_move and account_move.state == "posted" and account_move.payment_state != "paid" and account_move.payment_state != "in_payment":
                        _logger.info("Poste but not paid %s", account_move.payment_state)
                        confirm_payment = self.register_shopify_order_payment(account_move,shopify_connector.force_accounting_date,shopify_connector.payment_journal)
            else:
                _logger.info("THis is else of customer id")

    def create_shopify_order_invoice(self, order_id,force_accounting_date):
        _logger.info("create_shopify_order_invoice")
        invoices = order_id._create_invoices()
        if force_accounting_date:
            invoices.write({
                'invoice_date': order_id.date_order,
                'invoice_date_due': order_id.date_order,
            })
        _logger.info("invoices %s", invoices)
        return invoices, order_id.invoice_ids
    
    def shopify_order_invoice_post_entry(self, order_id):
        order_post_entry = order_id.action_post()
        return order_post_entry
    
    def register_shopify_order_payment(self, order_id,force_accounting_date,payment_journal):
        vals = {}
        if force_accounting_date:
            vals.update({'payment_date': order_id.invoice_date})
        if payment_journal:
            vals.update({'journal_id': payment_journal.id})
        register_payments = self.env['account.payment.register'].with_context(active_model='account.move', active_ids=order_id.ids).create(vals)
        register_payments.sudo()._create_payments()
        # payment = order_id.action_register_payment()
        # _logger.info("Payment %s", payment)
        # payment_id = payment['context']['active_ids']

        # if payment_id:
        #     payment_register = self.env['account.payment.register'].browse(payment_id)
        #     return payment_register.with_context({'active_model': 'account.move','active_ids': payment_id}).create({}).action_create_payments()
        
    def _shopify_address(self, order, shopify_customer_id, partner_data):
        res_partner = self.env['res.partner']
        if order.get('billingAddress'):
            # if order['billing_address']:
            billing_address = order['billingAddress']                
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
        if order.get('shippingAddress'):
            # if order['shipping_address']:
            shipping_address = order['shippingAddress']
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
        return order_billing_address, order_shipping_address
    
    def _create_address_dict(self, customer_id, address, address_type, parent_id=None):
        address_street = address.get('address1')
        address_street2 = address.get('address2')
        city = address.get('city')
        postcode = address.get('postcode')
        state = address.get('state')
        country = address.get('country')
        phone = address.get('phone')

        street = address_street if address_street != "" and address_street is not None else False
        street2 = address_street2 if address_street2 != "" and address_street2 is not None else False

        country_id, state_id = self._get_country_and_state_ids(country, state)

        return {
            'shopify_customer_id': customer_id,
            'parent_id': parent_id,
            'name': address.get('name', ''),
            'type': address_type,
            'street': street,
            'street2': street2,
            'city': city,
            'state_id': state_id,
            'zip': postcode,
            'country_id': country_id,
            'phone': phone,
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
            return coupon_data
        #     shopify_coupon = coupon_data.shopify_coupon_id
        #     response = requests.get(shop_url + "/price_rules/"+ shopify_coupon +".json")
        #     coupons = response.json()["price_rule"]
        #     if coupons:
        #         shopify_coupon = self.env['shopify.coupon']
        #         shopify_coupon.sync_coupon([coupons], shopify_connector, sync_type)
        # else:
        #     response = requests.get(shop_url + "/price_rules.json")
        #     coupons = response.json()["price_rules"]
        #     for coupon in coupons:
        #         if discount_code == coupon['title']:
        #             _logger.info("found matching coupon %s", discount_code)
        #             shopify_coupon = self.env['shopify.coupon']
        #             shopify_coupon.sync_coupon([coupon], shopify_connector, sync_type)
                
        #     coupon_data = coupon_program.sudo().search([('name', '=', discount_code),('shopify_store', '=', shopify_connector.id)])
        # _logger.info("This is fetch and sync coupon %s and reward id is %s", coupon_data, coupon_data.reward_ids)
        # return coupon_data
    
    def check_discount_type(self, discounts):
        for discount in discounts:
            if discount['type'] == 'manual':
                return True
        return False
    
    def _apply_coupon_on_order(self, coupon_data, existing_order):
        loyalty_card = self.env['loyalty.card']
        reward = self.env['loyalty.reward'].sudo().browse(coupon_data.reward_ids.id)

        # Create a coupon with the given loyalty program and points
        coupon_vals = {'program_id': coupon_data.id, 'points': 1}
        coupon_ids = loyalty_card.sudo().create(coupon_vals)
        coupon_code = coupon_ids.code
        
        # Apply the coupon to the order
        apply_coupon = existing_order._apply_program_reward(reward, coupon_ids)
        existing_order.write({'applied_coupon_ids':coupon_ids})

    def _apply_BXGY_on_order(self, coupon_data, existing_order):
        wizard = self.env['sale.loyalty.reward.wizard'].create({'order_id': existing_order.id,'selected_reward_id':coupon_data.reward_ids.id})
        coupon_vals = {'program_id': coupon_data.id, 'points': 2}
        coupon_ids = self.env['loyalty.card'].sudo().create(coupon_vals)
        existing_order.write({'applied_coupon_ids':coupon_ids})
        wizard.action_apply()
    
    def _fetch_product_by_name(self,order_product,shopify_connector):
        Product = self.env['product.product'].with_context(active_test=False,def_name='sync_product')
    
        product_data = Product.search([
            ('name', '=', order_product['name']),
            ('shopify_store', '=', shopify_connector.id),
            ('active', '=' , False)
        ])
        product_variant_archived = False
        if not product_data:
            _logger.info("Product not found, creating a new one.")
            product_data = Product.create({
                'name': order_product['name'],
                'shopify_store': shopify_connector.id,
                'active': False  # Ensure new product is active
            })
            product_variant_archived = product_data

            product_data.product_tmpl_id.with_context(def_name='sync_product').write({'active':False})
        else:
            product_variant_archived = product_data

        _logger.info("Product found/created: %s", product_variant_archived)

        return product_variant_archived

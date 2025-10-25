from odoo import api, fields, models
import requests
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class ShopifyCustomer(models.Model):
    _name = "shopify.customer"
    _description = "Shopify Customer"

    # def sync_customer(self, customers):
    #     res_partner = self.env['res.partner']
    #     for customer in customers:

    #         customer_id = customer['id']
    #         customer_email = customer['email']
    #         customer_first_name = customer['first_name']
    #         customer_last_name = customer['last_name']

    #         find_exists = res_partner.search([('shopify_customer_id', '=', customer_id),('parent_id', '=', False)])

    #         if 'default_address' in customer:
    #             default_address = customer['default_address']
    #             default_address_id = default_address['id']
    #             default_address_street = default_address['address1']
    #             default_address_street2 = default_address['address2']
    #             default_address_city = default_address['city']
    #             default_address_zip = default_address['zip']
    #             default_address_province_name = default_address['province']
    #             default_address_country_name = default_address['country_name']
                
    #             country_id = False
    #             state_id = False

    #             if default_address_country_name:
    #                 country = self.env['res.country'].search([('name', '=', default_address_country_name)])  
    #                 if country:
    #                     country_id = country.id                  
                
    #             if default_address_province_name:
    #                 state = self.env['res.country.state'].search([('name', '=', default_address_province_name)])
    #                 if state:
    #                     state_id = state.id
            
    #         customer_dict ={
    #             'shopify_customer_id': customer_id,
    #             'shopify_address_id': default_address_id,
    #             'name': customer_first_name +" " + customer_last_name,
    #             'street': default_address_street,
    #             'street2': default_address_street2,
    #             'city': default_address_city,
    #             'zip':default_address_zip,
    #             'state_id': state_id,
    #             'country_id':country_id,
    #             'email':customer_email
    #         }

    #         if find_exists:
    #             update_customer = find_exists.write(customer_dict)
    #             if update_customer:
    #                 res_partner_id = find_exists
    #         else:
    #             customer_create = res_partner.create(customer_dict)
    #             if customer_create:
    #                 res_partner_id = customer_create

    #         if len(customer['addresses']) > 1:
    #             for extra_address in customer['addresses']:
    #                 if not extra_address['default']:
    #                     extra_address_name = extra_address['name']
    #                     extra_address_id = extra_address['id']
    #                     extra_address_street = extra_address['address1']
    #                     extra_address_street2 = extra_address['address2']
    #                     extra_address_city = extra_address['city']
    #                     extra_address_zip = extra_address['zip']
    #                     extra_address_province_name = extra_address['province']
    #                     extra_address_country_name = extra_address['country_name']

    #                     extra_address_country_id = False
    #                     extra_address_state_id = False

    #                     if extra_address_province_name:
    #                         extrs_country = self.env['res.country'].search([('name', '=', extra_address_country_name)])  
    #                         if extrs_country:
    #                             extra_address_country_id = extrs_country.id                  
                
    #                     if extra_address_country_name:
    #                         extra_state = self.env['res.country.state'].search([('name', '=', extra_address_province_name)])
    #                         if extra_state:
    #                             extra_address_state_id = extra_state.id

    #                     customer_extra_address_dict ={
    #                         'parent_id': res_partner_id.id,
    #                         'type':'delivery',
    #                         'shopify_customer_id': customer_id,
    #                         'shopify_address_id': extra_address_id,
    #                         'name': extra_address_name,
    #                         'street': extra_address_street,
    #                         'street2': extra_address_street2,
    #                         'city': extra_address_city,
    #                         'zip':extra_address_zip,
    #                         'state_id': extra_address_state_id,
    #                         'country_id':extra_address_country_id
    #                     }
                        
    #                     find_exists_extra_address = res_partner.search([('parent_id', "=", res_partner_id.id),('shopify_address_id', '=', extra_address_id),('shopify_customer_id', '=', customer_id)])
                        
    #                     if find_exists_extra_address:
    #                         update_extra_address = find_exists_extra_address.write(customer_extra_address_dict)
    #                     else:
    #                         create_extra_address = res_partner.create(customer_extra_address_dict)

    def sync_customer(self, customers, shopify_connector, sync_type):
        res_partner = self.env['res.partner']
        _logger.info("customer %s", customers)
        existing_customers = res_partner.search([('is_shopify_customer', '=', True),('parent_id', '=', False),('shopify_store', '=', shopify_connector.id)])
        exclude_ids = []
        for ex_cust in existing_customers:
            exclude_ids.append(ex_cust.shopify_customer_id)
        #_logger.info("this is all ids exist in odoo %s", exclude_ids)
        self = self.with_context(def_name='sync_customer')
        for customer in customers:
            if str(customer['id']) in exclude_ids and sync_type == "sync_button":
                _logger.info("This is match ids %s", customer['id'])
                continue
            customer_id = customer['id']
            customer_email = customer['email']
            customer_first_name = customer['first_name']
            customer_last_name = customer['last_name']

            default_address = customer.get('default_address', {})
            customer_dict = self._prepare_customer_dict(customer, default_address, shopify_connector)
            res_partner_id = self._sync_customer_record(res_partner, customer_id, customer_dict, shopify_connector)

            if len(customer['addresses']) > 1:
                self._sync_extra_addresses(res_partner, res_partner_id, customer['addresses'], customer_id, shopify_connector)

    def _prepare_customer_dict(self, customer, default_address, shopify_connector):
        default_address_id = default_address.get('id')
        default_address_street = default_address.get('address1')
        default_address_street2 = default_address.get('address2')
        default_address_city = default_address.get('city')
        default_address_zip = default_address.get('zip')
        default_address_province_name = default_address.get('province')
        default_address_country_name = default_address.get('country_name')
        default_address_mobile = default_address.get('phone')

        country_id, state_id = self._get_country_and_state_ids(default_address_country_name, default_address_province_name)
        _logger.info("add1 and add2 customer function default address%s %s", default_address_street, default_address_street2)
        if default_address_street == "" or default_address_street is None:
            _logger.info("this default_address_street is none or blank")
        if default_address_street2 == "" or default_address_street2 is None:
            _logger.info("this default_address_street2 is none or blank")
        
        street = default_address_street if default_address_street != "" and default_address_street is not None else False
        street2 = default_address_street2 if default_address_street2 != "" and default_address_street2 is not None else False

        return  {
            'shopify_customer_id': customer['id'],
            'shopify_address_id': default_address_id,
            'shopify_store': shopify_connector.id,
            'is_shopify_customer':True,
            'name': f"{customer['first_name']} {customer['last_name']}",
            'street': street,
            'street2': street2,
            'city': default_address_city,
            'zip': default_address_zip,
            'state_id': state_id,
            'country_id': country_id,
            'email': customer['email'],
            'mobile': default_address_mobile if default_address_mobile else False
        }

    def _get_country_and_state_ids(self, country_name, province_name):
        country_id, state_id = False, False

        if country_name:
            country = self.env['res.country'].search([('name', '=', country_name)])
            if country:
                country_id = country.id

        if province_name:
            state = self.env['res.country.state'].search([('name', '=', province_name),('country_id','=',country_id)])
            if state:
                state_id = state.id

        return country_id, state_id

    def _sync_customer_record(self, res_partner, customer_id, customer_dict, shopify_connector):
        find_exists = res_partner.search([('shopify_customer_id', '=', customer_id), ('parent_id', '=', False), ('shopify_store', '=', shopify_connector.id)])
        if find_exists:
            _logger.info("customer_dict %s",customer_dict)
            find_exists.write(customer_dict)
            return find_exists
        else:
            return res_partner.create(customer_dict)

    def _sync_extra_addresses(self, res_partner, parent_record, addresses, customer_id, shopify_connector):
        for extra_address in addresses:
            if not extra_address['default']:
                extra_address_dict = self._prepare_extra_address_dict(extra_address, parent_record.id, customer_id, shopify_connector)
                find_exists_extra_address = res_partner.search([('parent_id', "=", parent_record.id),('shopify_address_id', '=', extra_address_dict['shopify_address_id']),('shopify_customer_id', '=', customer_id)
                ])

                if find_exists_extra_address:
                    find_exists_extra_address.write(extra_address_dict)
                else:
                    res_partner.create(extra_address_dict)

    def _prepare_extra_address_dict(self, extra_address, parent_id, customer_id, shopify_connector):
        extra_address_id = extra_address.get('id')
        extra_address_street = extra_address.get('address1')
        extra_address_street2 = extra_address.get('address2')
        extra_address_city = extra_address.get('city')
        extra_address_zip = extra_address.get('zip')
        extra_address_province_name = extra_address.get('province')
        extra_address_country_name = extra_address.get('country_name')
        extra_address_mobile = extra_address.get('phone')

        extra_address_country_id, extra_address_state_id = self._get_country_and_state_ids(extra_address_country_name, extra_address_province_name)
        _logger.info("add1 and add2 customer function extra address%s %s", extra_address_street, extra_address_street2)
        
        street = extra_address_street if extra_address_street != "" and extra_address_street is not None else False
        street2 = extra_address_street2 if extra_address_street2 != "" and extra_address_street2 is not None else False

        if extra_address_street == "" or extra_address_street is None:
            _logger.info("this extra_address_street is none or blank")
        if extra_address_street2 == "" or extra_address_street2 is None:
            _logger.info("this extra_address_street2 is none or blank")

        return {
            'parent_id': parent_id,
            'type': 'delivery',
            'shopify_customer_id': customer_id,
            'shopify_address_id': extra_address_id,
            'shopify_store': shopify_connector.id,
            'is_shopify_customer': True,
            'name': extra_address.get('name'),
            'street': street,
            'street2': street2,
            'city': extra_address_city,
            'zip': extra_address_zip,
            'state_id': extra_address_state_id,
            'country_id': extra_address_country_id,
            'mobile': extra_address_mobile if extra_address_mobile else False
        }




        
        
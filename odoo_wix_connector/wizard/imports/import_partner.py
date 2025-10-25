# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import models
from odoo.tools.translate import _

class Importwoocommercepartners(models.TransientModel):
    _name = "import.wix.partners"
    _inherit = 'import.partners'
    _description = "Import Wix Partners"

    def import_now(self,channel_id,sdk,kwargs):
        data_list = []
        if kwargs.get('filter_on') == "store_id":
            return self._get_customer_by_id(channel_id, sdk, kwargs), kwargs
        current_page = kwargs.pop('current_page') if kwargs.get('current_page') else 0
        kwargs.update({'current_page':current_page})
        customers= channel_id.fetch_wix_customers_data(sdk,kwargs)
        if customers:
            if kwargs.get('filter_on') or kwargs.get('from_cron'):
                total_customers = customers.get('pagingMetadata').get('total')
                kwargs = channel_id.wix_pagination(kwargs, total_customers)
            for customer in customers.get('contacts'):
                data_list.append(self._get_contact_address(channel_id,customer))
            if kwargs.get('from_cron'):
                from datetime import datetime
                createdDate = customers.get('contacts')[-1].get('createdDate').replace('T',' ').split('.')[0]
                channel_id.import_customer_date = datetime.strptime(createdDate,"%Y-%m-%d %H:%M:%S")
        return data_list, kwargs


    def _get_contact_address(self,channel_id,data):
        shipping,billing,other_address,customer_address,phone={},{},[],{},None
        if data:
            store_id = data.get('id')
            primary_info=data.get('primaryInfo')
            info=data.get('info')
            name=  info.get('name')
            emails= info.get('emails')
            customer_address.update({
                    'channel_id': channel_id.id,
                    'store_id'  : data.get('id'),
                    'name'      : name.get('first') if name else False,
                    'last_name' : name.get('last') if name else False,
                    'email'     : primary_info.get('email'),
                    'phone'     : primary_info.get('phone'),
                    'contacts' : []
                    })
            if info.get('phones') and info.get('phones').get('items') and info.get('phones').get('items')[0].get('phone'):
                phone= info.get('phones').get('items')[0].get('phone')
            
            if info.get('addresses') and info.get('addresses').get('items'):
                addresses=info.get('addresses').get('items')
                for address in addresses:
                    if address.get('tag')=='SHIPPING':
                        shipping.update(address.get('address'))
                    if address.get('tag')=='BILLING':
                        billing.update(address.get('address'))
                    else:
                        other_address.append(address)
                customer_address.update({
                    'channel_id': channel_id.id,
                    'store_id'  : data.get('id'),
                    'name'      : name.get('first') if name else False,
                    'last_name' : name.get('last') if name else False,
                    'email'     : primary_info.get('email'),
                    'phone'     : primary_info.get('phone'),
                    'contacts' : []
                    })
            for other in other_address:
                customer_address['contacts'].append(
                    {
                        'channel_id'  : channel_id.id,
                        'parent_id'   : store_id,
                        'store_id'    : f'other_{store_id}',
                        'type'        : 'contact',
                        'name'        : name.get('first') if name else False,
                        'last_name'   : name.get('last') if name else False,
                        'street'      : other.get('addressLine'),
                        # 'street2'     : data['billing'].get('address_2'),
                        'city'        : other.get('city'),
                        'state_code'  : other.get('subdivision'),
                        'country_code': other.get('country'),
                        'zip'         : other.get('postalCode'),
                        'email'       : emails.get('items')[0].get('email') if emails else False,
                        'phone'       :  phone,
                    })
            if billing:
                customer_address['contacts'].append(
                      {
                        'channel_id'  : channel_id.id,
                        'parent_id'   : store_id,
                        'store_id'    : f'billing_{store_id}',
                        'type'        : 'invoice',
                         'name'       : name.get('first') if name else False,
                        'last_name'   : name.get('last') if name else False,
                        'street'      : billing.get('addressLine'),
                        # 'street2'     : data['billing'].get('address_2'),
                        'city'        : billing.get('city'),
                        'state_code'  : billing.get('subdivision'),
                        'country_code': billing.get('country'),
                        'zip'         : billing.get('postalCode'),
                        'email'       : emails.get('items')[0].get('email') if emails else False,
                        'phone'       :  phone,
                    })
               
            if shipping:
               customer_address['contacts'].append(
                      {
                        'channel_id'  : channel_id.id,
                        'parent_id'   : store_id,
                        'store_id'    :  f'shipping_{store_id}',
                        'type'        : 'delivery',
                         'name'       : name.get('first') if name else False,
                        'last_name'   : name.get('last') if name else False,
                        'street'      : shipping.get('addressLine'),
                        # 'street2'     : data['billing'].get('address_2'),
                        'city'        : shipping.get('city'),
                        'state_code'  : shipping.get('subdivision'),
                        'country_code': shipping.get('country'),
                        'zip'         : shipping.get('postalCode'),
                        'email'       : emails.get('items')[0].get('email') if emails else False,
                        'phone'       :  phone,
                    })
            return customer_address


    def _get_customer_by_id(self, channel_id, sdk, kwargs):
        customer = channel_id.fetch_wix_customers_data(sdk, kwargs)
        return [self._get_contact_address(channel_id, customer.get('contact'))]

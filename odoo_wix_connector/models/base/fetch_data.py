# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from datetime import datetime

from odoo import models, api, _


MageDateTimeFomat = '%Y-%m-%d %H:%M:%S'

class MultiChannelSale(models.Model):
    _inherit = 'multi.channel.sale'
    @api.model
    def _fetch_wix_category(self, sdk,**kwargs):
        filter_group = 0
        category_ids=[]
        operation_params = self._fetch_wix_params(filter_group = filter_group, **kwargs)
        if kwargs.get('filter_on') and kwargs.get('filter_on') != 'all':
            if operation_params.get("field") == "id" or kwargs.get('filter_on') == 'store_id':
                if operation_params['value']:
                    category_ids.append(sdk.get_categories(id=operation_params['value'],params=operation_params).get('data').get('data').get('category'))
                    return category_ids
        category_ids=sdk.get_categories().get('data').get('data').get('categories').get('data')
        return category_ids

    @api.model
    def _fetch_wix_order_data(self, sdk, **kwargs):
        filter_group ,count = 0, 0
        orders_data,message=[],''
        operation_params = self._fetch_wix_params(filter_group = filter_group, **kwargs)
        if kwargs.get('wix_next_url'):
            operation_params.update({'wix_next_url': kwargs.get('wix_next_url')})
        if kwargs.get('filter_on') and kwargs.get('filter_on') != 'all' :
            if operation_params.get("field") == "id" or kwargs.get('filter_on') == 'store_id' :
                param1=operation_params.get('param1') if operation_params.get('param1') else 0
                if kwargs.get('filter_on') == 'store_id': param1 = kwargs.get('store_id')
                if param1:
                    id_list=param1.replace(" ", "").split(',')
                    orders_data=sdk.get_Order(Id = id_list,params = operation_params)
                    return orders_data

            if operation_params.get('field') == "status" and operation_params.get('value'):
                # importing orders according to status
                orders_data=sdk.get_Orders(params = operation_params)
                return orders_data
            if operation_params.get('field') == "orderDate":
                orders_data=sdk.get_Orders(params = operation_params)
                return orders_data
            orders_data={'orders': orders_data}
            return dict(
            data= orders_data,
            message=message,
            total_count=count)
        orders_data=sdk.get_Orders(params = operation_params)
        return orders_data
    
    @api.model
    def fetch_wix_customers_data(self,sdk,kwargs):
        customer_data=[]
        param_filter=None
        operation_params = self._fetch_wix_params(filter_group=0,**kwargs)
        if kwargs.get('filter_on') and kwargs.get('filter_on') != 'all':
            if operation_params.get("field") == "id" or kwargs.get('filter_on') == 'store_id':
                param1=operation_params.get('param1') if operation_params.get('param1') else 0
                param2=  operation_params.get('param2') if operation_params.get('param2') else operation_params.get('param1')
                if kwargs.get('filter_on') == 'store_id' : param1 = kwargs.get('store_id')
                if param1 or param2:
                    param_filter = param1 if param1 else param2 
                # for id in range(param1,param2+1):
                    operation_params['value']=param_filter
                    customer_data = sdk.get_customer(Id=param_filter,params=operation_params).get('data')
            elif operation_params.get("field") == "email":
                customer_data=sdk.get_customers(params=operation_params).get('data')
            elif operation_params.get('field') == "orderDate":
                customer_data = sdk.get_customers(params=operation_params).get('data')
            return customer_data
        return sdk.get_customers(params=operation_params).get('data')

    @api.model
    def _fetch_wix_params(self,filter_group = 0,**kwargs):
        params = dict()
        params.update(self.get_search_criteria(filter_group,**kwargs))
        if  kwargs.get('page_size'):
            params["[page_size]"]=kwargs.get('page_size') if kwargs.get('page_size')<=100 else 100
        if  kwargs.get('current_page'):
            params["[current_page]"]=kwargs.get('current_page')
        if kwargs.get('fields'):
            params["fields"]=(kwargs.get('fields'))
        return params

    @api.model
    def _fetch_wix_product_data(self,sdk,**kwargs):
        message, params, total_count, filter_group ='', dict(), 0, 0
        operation_params = self._fetch_wix_params(filter_group = filter_group,**kwargs)
        products_data=[]
        if kwargs.get('filter_on') and kwargs.get('filter_on') != 'all' :
            operation_params = self._fetch_wix_params(filter_group = filter_group, **kwargs)
            count=0
            if operation_params.get("field") == "id" or kwargs.get('filter_on') == 'store_id':
                ids_list=kwargs.get('store_id').replace(" ", "").split(',')
                product=sdk.get_product(Id=ids_list, params=operation_params)
                if product:
                    products_data = product.get('data').get('products')
                    count = product.get('data').get('totalResults')
            elif kwargs.get('filter_on') == "date_range":
                res = sdk.get_products(params=operation_params)
                if res:
                    products_data = res.get('data').get('products')
                    count = res.get('data').get('totalResults')
            products_data={'products': products_data}
            return dict(
            data= products_data,
            message=message,
            total_count=count)
        if len(operation_params):
            params.update(operation_params)
        res = sdk.get_products(params=operation_params)
        message+=res.get('message')
        data=res.get('data')    
        if data and data.get('totalResults'):
            total_count = data.get('totalResults')
        return dict(
            data=data,
            message=message,
            total_count=total_count
        )
        
    @staticmethod
    def get_search_criteria(filter_group, **kwargs):
        param1 = param2 = field = None
        param = dict()
        parameq = paramin = None
        if kwargs.get('filter_on') == "date_range":
            param1 = kwargs.get('start_date')
            param2 = kwargs.get('end_date')
            field = "orderDate"
            if param1:
                param1 = param1.strftime(MageDateTimeFomat)
            if param2:
                param2 = param2.strftime(MageDateTimeFomat)
        elif kwargs.get('filter_on') == "category_id":
            parameq = kwargs.get('category_id')
            field = 'id'
        elif kwargs.get('filter_on') == "customer_id":
            parameq = kwargs.get('customer_email')
            field = "email"
        elif kwargs.get('filter_on') == "on_id": #specifically for runtime creation process
            parameq = kwargs.get('id')
            field = "id"
        elif kwargs.get('order_state'):
            field = 'status'
            parameq=kwargs.get('order_state')
        elif kwargs.get('from_cron') and kwargs.get('wix_import_date_from'):
            # import for cron
            kwargs.update({'filter_on': 'date_range'})
            kwargs.update({'start_date':kwargs.get('wix_import_date_from')}) if not kwargs.get('start_date') else False
            kwargs.update({'end_date':datetime.now()}) if not kwargs.get('end_date') else False
            param1 = kwargs.get('start_date')
            param2 = kwargs.get('end_date')
            field = "orderDate"
            if param1:
                param1 = param1.strftime(MageDateTimeFomat)
            if param2:
                param2 = param2.strftime(MageDateTimeFomat)
        if param1 and param2:
            param = {
            "field":field,
            "param1":param1,
            }
            filter_group += 1
            param.update({
                "field":field,
                "param2":param2
            })
        elif param1:
            param = {
                "field": field,
                "param1": param1
               
            }
        elif param2:
            
            param = {
               "field": field,
                "param2": param2
            }
        elif parameq:
           
            param = {
                "field":field,
                "value": parameq,
            }
        elif paramin:
            param = {
                "field": field,
                "value": paramin,
            }
        else:
            return {}
        return param

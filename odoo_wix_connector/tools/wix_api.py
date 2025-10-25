# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
import json
import requests
from datetime import datetime
from logging import getLogger
_logger = getLogger(__name__)


def p_decorate(func):
	def func_wrapper(self,*args, **kwargs):
		response=None
		res = dict(
			data = None,
			message = ''
		)
		try:
			response = func(self,*args, **kwargs)
			if response.ok:
			# if type(response)==requests.models.Response:
				if response.status_code > 201:
					content = response.content
					code = response.status_code
					res['message']+='API returned %s response: %s' % (code, content)
				else:
					try:
						res['data'] = response.json()
					except Exception as e:
						res['message']+=response.text
			else:
				_logger.error('Error: %r',response.content)
		except Exception as e:
			_logger.error('Error: Api Calling Error: %r', e, exc_info=True)
			res['message']+=str(e)
		return res
	return func_wrapper


class Wix(object):

	def __init__(self, *args, **kwargs):
		self.appId=kwargs.get('APP_ID')
		self.appsecret=kwargs.get('APP_SECRET')
		self.grant_type = kwargs.get('grant_type')
		self.base_uri = kwargs.get('base_uri')
		self.oauth_token  = kwargs.get('access_token')
		self.debug  = kwargs.get('debug', False)
		if kwargs.get('APP_SECRET') and kwargs.get('APP_ID') and kwargs.get('access_token'):
			oauth_token_res = self._get_oauth_token()
			self.oauth_token = oauth_token_res.get('data')

	# def get_auth_header(self): # method to get common header
	# 	return {
	# 		'Content-Type' : 'application/json',
	# 		'Authorization': str(self.oauth_token.get('access_token')),
	# 	}

	@p_decorate
	def _get_data(self,url,data=None,params=None,headers={},auth=False):
		headers.update({
			'Content-Type' : 'application/json',
		})
		if auth:
			headers['Authorization']=self.oauth_token.get("access_token")
		params = params or dict()
		res =   requests.get(
			url,
			params=params,
			headers=headers,
			# data=json.dumps(data),
		)
		return res

	@p_decorate
	def _patch_data(self,url,data=None,params=None,headers={},auth=False):
		headers.update({
			'Content-Type' : 'application/json',
		})
		if auth:
			headers['Authorization']=self.oauth_token.get("access_token")
		params = params or dict()
		res =   requests.patch(
			url,
			params=params,
			headers=headers,
			data=json.dumps(data) if data else {},
		)
		return res

	@p_decorate
	def _post_data(self,url,data=None,files=None,params={},headers=None,auth=False):
		if not headers:
			headers={
				'Content-Type' : 'application/json'
			}
		if auth:
			headers['Authorization']=self.oauth_token.get("access_token")
		data = data or dict()
		res= requests.post(
				url,
				headers=headers, 
				params = params if params else False,
				data=json.dumps(data) if data else False,
				allow_redirects=False,
				timeout=30, 
			  )
		return res

	def _get_oauth_token(self):
		headers= {'Content-Type' : 'application/json'}
		data = dict(
			refresh_token = eval(self.oauth_token).get('refresh_token'),
			client_secret = self.appsecret,
			client_id     = self.appId,
			grant_type    = self.grant_type,
		)
		endpoint = self.base_uri
		return self._post_data(endpoint,data,headers,headers={})

	def get_pagination_data(self, params):
		return {
				"query": {
				"paging": { 
					"limit": params.get('[page_size]'), 
					"offset": params.get('[current_page]') if params.get('[current_page]') else 0
					}
				}
			}

	def convert_date_time(self, params):
		param1 = datetime.strptime(params.get('param1'),'%Y-%m-%d %H:%M:%S')
		param2 = datetime.strptime(params.get('param2'),'%Y-%m-%d %H:%M:%S')
		param2 = int(datetime.timestamp(param2)*1000)
		param1 = int(datetime.timestamp(param1)*1000)
		return param1, param2

	def get_collections(self):
		endpoint ="https://www.wixapis.com/stores/v1/collections/query"	
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		return self._post_data(endpoint,data={},headers=headers,auth=True)

	def get_collection(self, id):
		endpoint = f"https://www.wixapis.com/stores/v1/collections/{id}"
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		return self._get_data(endpoint,headers=headers,auth=True)

	def get_products(self,params=None):
		data = {}
		endpoint = 'https://www.wixapis.com/stores/v1/products/query'
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		if params:
			if params.get('field') == "orderDate":
				# importing products using date_range field(using last updated date)
				param1, param2 = self.convert_date_time(params)
				data = {
					"query": {
						"filter": json.dumps({
							"$and": [{
								"createdDate":{"$lte":param2
								}}, 
								{"createdDate":{"$gte":param1
								}}
							]}), 
							"paging": {
								"limit": params.get('[page_size]'), 
								"offset": params.get('[current_page]') if params.get('[current_page]') else 0
							},
							"sort": json.dumps([{"numericId":"asc"}])
							}}
			else:
				data = self.get_pagination_data(params)
				data['query'].update({'sort':json.dumps([{"numericId":"asc"}])})
			data.update({'includeVariants': True, 'includeHiddenProducts': True}) # Variants & Hidden Product(from store) included in response
		return self._post_data(endpoint,data=data,headers=headers,auth=True)

	def get_product(self,Id=None,params=None):
		# endpoint ='https://www.wixapis.com/stores/v1/products/{id}'.format(id=Id)
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		endpoint = 'https://www.wixapis.com/stores/v1/products/query'
		data = {
				"query": {
					"filter":json.dumps({"id": { "$hasSome": Id} }), 
						"sort": json.dumps([{"numericId":"asc"}])
						}}
		data.update({'includeVariants': True, 'includeHiddenProducts': True})
		return self._post_data(endpoint,data=data,headers=headers,auth=True)

		# return self._get_data(endpoint,headers=headers,auth=True)

	def get_customers(self,params=None):
		data = {}
		endpoint = "https://www.wixapis.com/contacts/v4/contacts/query"
		headers={"Authorization": str(self.oauth_token.get("access_token")),
		'Content-Type':'application/json'}
		if params:
			if params.get('field') == "email":
				# importing contact with email
				data = {
					"query": {
						"filter": {
							"info.emails.email": params.get('value')
						}
					}
				}
			elif params.get('field') == "orderDate":
				param1 = datetime.strptime(params.get('param1'),'%Y-%m-%d %H:%M:%S').isoformat()
				param2 = datetime.strptime(params.get('param2'),'%Y-%m-%d %H:%M:%S').isoformat()
				data = {
					"query": {
						"filter": {
							"$and": [{
								"createdDate":{"$lte":param2
								}}, 
								{"createdDate":{"$gte":param1
								}}
							]}, 
							"paging": { 
								"limit": params.get('[page_size]'), 
								"offset": params.get('[current_page]') if params.get('[current_page]') else 0
							},
							}}
			else:
				data = self.get_pagination_data(params)
		return self._post_data(endpoint,data=data,headers=headers,auth=True)

	def get_customer(self,Id=None,params=None):
		endpoint ='https://www.wixapis.com/contacts/v4/contacts/{id}'.format(id=Id)
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		return self._get_data(endpoint,headers=headers,auth=True)

	def get_Orders(self,params=None):
		data = {}
		endpoint = 'https://www.wixapis.com/ecom/v1/orders/search'
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		if params.get('field'):
			data = self.get_order_data_params(params)
		else:
			data = {
				"search": {
					"cursor_paging": { 
					"limit": params.get('[page_size]'), 
					"offset": params.get('[current_page]') if params.get('[current_page]') else 0,
					},
					"sort": [
						{
						"fieldName": "createdDate",
						"order": "AESC"
						}
					],
				}
			}
		if params.get('wix_next_url'):
			data['search']['cursor_paging']['cursor'] = params.get('wix_next_url')
		return self._post_data(endpoint,data=data,headers=headers,auth=True)

	def get_order_data_params(self, params):
		if params.get('field') == "status" and params.get('value'):
			# imported by order status
			return {
                 "search": {
                   "filter": {"paymentStatus": params.get('value')},
                   "cursor_paging": {
                     "limit": params.get('[page_size]'),
					 "offset": params.get('[current_page]') if params.get('[current_page]') else 0
                   },
                   "sort":	[
								{
								"fieldName": "createdDate",
								"order": "AESC"
								}
							]
							}
						}
		elif params.get('field') == 'orderDate' and params.get('param1') and params.get('param2'):
			# Import by date range filter using order created date
			param1, param2 = self.convert_date_time(params)
			return {
				"search": {
					"filter": {
						"$and": [{
							"createdDate":{"$lte":param2
							}}, 
							{"createdDate":{"$gte":param1
							}}
						]}, 
						"cursor_paging": { 
							"limit": params.get('[page_size]'), 
							"offset": params.get('[current_page]') if params.get('[current_page]') else 0
						},
							"sort": [{
								"fieldName": "number",
								"order": "AESC"
								}]
						}}
		return False

	def get_Order(self,Id=None,params=None):
		# endpoint ='https://www.wixapis.com/ecom/v1/orders/{id}'.format(id=Id)
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		endpoint = 'https://www.wixapis.com/ecom/v1/orders/search'
		data = {
				"search": {
					"filter":{"id": { "$hasSome": Id}}, 
						"sort": [{
								"fieldName": "createdDate",
								"order": "ASC"
								}]
						}}
		return self._post_data(endpoint,data=data,headers=headers,auth=True)


	def create_collection(self,data):
		endpoint='https://www.wixapis.com/stores/v1/collections'
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		return self._post_data(endpoint,data=data,headers=headers,auth=True)

	def create_product(self,data):
		endpoint='https://www.wixapis.com/stores/v1/products'
		data={
      			'product':data
			}
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		return self._post_data(endpoint,data=data,headers=headers,auth=True)

	def update_product(self,Id=None,data={}):
		endpoint='https://www.wixapis.com/stores/v1/products/{ID}'.format(ID=Id)
		data={
      			'product':data}
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		return self._patch_data(endpoint,data=data,headers=headers,auth=True)

	def reset_product_variants(self, id):
		# Every time when we are updating product this api is called
		endpoint = f"https://www.wixapis.com/stores/v1/products/{id}/variants/resetToDefault"
		data = {}
		return self._post_data(endpoint,data=data,auth=True)
  
	def update_variant_product(self,Id=None,data={}):
		endpoint='https://www.wixapis.com/stores/v1/products/{ID}/variants'.format(ID=Id)
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		return self._patch_data(endpoint,data=data,headers=headers,auth=True)


	def update_quantity_realtime(self, data, id):
		endpoint = "https://www.wixapis.com/stores/v2/inventoryItems/product/{ID}".format(ID = id)
		headers ={
			'Content-Type' : 'application/json',
		}
		headers['Authorization']=self.oauth_token.get("access_token")
		res = requests.patch(
			endpoint,
			headers=headers,
			data=json.dumps(data),
		)
		if not res.ok:
			_logger.info('Error: Something went wrong in updating quantity %r',res.json())
			return False
		return True

	def update_collection(self,Id=None,data={}):
		endpoint='https://www.wixapis.com/stores/v1/collections/{ID}'.format(ID=Id)
		data={'collection':data}
		headers={"Authorization": str(self.oauth_token.get("access_token"))}
		response = requests.patch(endpoint,headers=headers,data=json.dumps(data))
		if response.ok:
			return response.json()
		return False

	def add_product_to_collection(self, product_store_id, collection_store_ids):
		endpoint = f"https://www.wixapis.com/stores/v1/collections/{collection_store_ids}/productIds"
		data = {
                     "productIds": [
                         product_store_id
                     ]
                   }
		return self._post_data(endpoint,data=data,auth=True)

	def order_fullfillment(self,id,data):
		endpoint=f"https://www.wixapis.com/ecom/v1/fulfillments/orders/{id}/create-fulfillment"
		data={"fulfillment":data}
		headers={
			"Authorization": str(self.oauth_token.get("access_token")),
			"Content-Type" : 'application/json'
			}
		response = requests.post(endpoint,headers=headers,data=json.dumps(data))
		if response.ok:
			return True
		_logger.info("Error: %r",response.json())
		return False

	def add_product_media(self, product_id, image_url):
		headers={
			"Authorization": str(self.oauth_token.get("access_token")),
			"Content-Type": "application/json"
		}
		payload = {
			"media":[
				{
					"url":str(image_url)
				}
			]
		}
		endpoint = f"https://www.wixapis.com/stores/v1/products/{product_id}/media"
		response = requests.post(endpoint,headers=headers,data=json.dumps(payload))
		if not response.ok:
			_logger.info('Error in adding image media to product: %r',response.json())
			return False
		return True

	# Getting quantity of products during import
	def get_product_quantity(self, inventoryId):
		endpoint = f"https://www.wixapis.com/stores/v2/inventoryItems/{inventoryId}/getVariants"
		return self._post_data(endpoint, auth = True)

if __name__ =='__main__':
	pass

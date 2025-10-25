# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import http
from odoo.http import request
from werkzeug.utils import redirect
from ..tools.help import getTokensFromWix,getAccessToken,getDefaultparameters#,getInstance,getProducts,getOrders,


class Wix(http.Controller):
    @http.route('/wix/login/<string:instance_number>', type='http', auth="public", website=True,methods=['GET'], csrf=False)
    def login(self, instance_number, **kwargs):
        channel_id = request.env['multi.channel.sale'].search([('channel','=','wix'),('id','=',int(instance_number))])
        if channel_id and kwargs.get('code'):
            data = {
                'url':getDefaultparameters().get("AUTH_PROVIDER",{}) + '/access',
                'client_secret': channel_id.wix_app_secret_key,
                'client_id': channel_id.wix_app_id,
            }
            tokens_data = {
                'code': kwargs.get('code'),
                'grant_type': "authorization_code"
                }
            tokens_data.update(data)
            tokens=getTokensFromWix(tokens_data)
            if tokens.get('refresh_token'):
                refresh_token=tokens.get('refresh_token')
                refresh_data={
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"}
                refresh_data.update(data)
                refresh_token_update = getAccessToken(refresh_data) # refresh token here
                if refresh_token_update:
                    channel_id.sudo().write({
                        "wix_access_token": refresh_token_update, 
                        'state': 'validate'
                    })
        return request.redirect(self.get_instance_redirect_url(instance_number))
    
    # It will be called when we create connection from wix end
    @http.route('/wix/signup/<string:instance_number>', type='http', auth="public", methods=['GET'], csrf=False)
    def sign_up(self,instance_number,**kwargs):
        credentials_rec=request.env['multi.channel.sale'].search([('channel','=','wix'),('id','=',int(instance_number))])
        if credentials_rec:
            APP_ID = credentials_rec.wix_app_id
            permissionRequestUrl= getDefaultparameters().get("permissionRequestUrl",{})
            redirectUrl = credentials_rec.wix_base_redirectUrl
            token = kwargs.get("token")
            if token:
                returnUrl= permissionRequestUrl+"?"+"token="+token+"&"+"appId="+APP_ID+"&"+"redirectUrl="+redirectUrl+ "/wix/login/"+instance_number
                return redirect(returnUrl)
        return "Token wix Not found"
    
    
    # @http.route('/product/<string:instance_number>', type='http', auth="public", website=False,methods=['GET'], csrf=False)
    # def product(self,instance_number,**kwargs):
    #     credentials_rec=request.env['multi.channel.sale'].search([('channel','=','wix'),('id','=',int(instance_number))])
    #     # global access_token
    #     access_token = eval(credentials_rec.wix_access_token)
    #     AUTH_PROVIDER = 'https://www.wix.com/oauth'
    #     STORE_CATALOG_API_URL = 'https://www.wixapis.com/stores/v1'
    #     APP_ID = 'd7a7f0ca-c0fd-4e4f-97a6-de6c42ab966a'
    #     APP_SECRET = 'f4fbb0e1-87a6-4d4b-9dbd-6545640e088c'
    #     refresh_token=access_token.get('refresh_token')
    #     data={"url":AUTH_PROVIDER +'/access', "refresh_token": refresh_token,
    #           "client_secret": APP_SECRET,
    #           "client_id": APP_ID,
    #           "grant_type": "refresh_token"}
    #     refresh_token_update = getAccessToken(data)
    #     credentials_rec.sudo().write({"wix_access_token":refresh_token_update})
    #     access_token = refresh_token_update
    #     data={"url":STORE_CATALOG_API_URL+'/products/query', "access_token": refresh_token_update.get('access_token')}
    #     product_data=getProducts(data)
    #     return request.render('odoo_wix_connector.wix_controller', {})
    
    # @http.route('/order/<string:instance_number>', type='http', auth="public",website=False, methods=['GET'], csrf=False)
    # def order(self,instance_number,**kwargs):
    #     credentials_rec=request.env['multi.channel.sale'].search([('channel','=','wix'),('id','=',int(instance_number))])
    #     # global access_token
    #     access_token = eval(credentials_rec.wix_access_token)
    #     AUTH_PROVIDER = 'https://www.wix.com/oauth'
    #     STORE_ORDERS_API_URL = 'https://www.wixapis.com/stores/v2'
    #     APP_ID = 'd7a7f0ca-c0fd-4e4f-97a6-de6c42ab966a'
    #     APP_SECRET = 'f4fbb0e1-87a6-4d4b-9dbd-6545640e088c'
    #     refresh_token=access_token.get('refresh_token')
    #     data={"url":AUTH_PROVIDER +'/access', "refresh_token": refresh_token,
    #            "client_secret": APP_SECRET,
    #             "client_id": APP_ID,
    #             "grant_type": "refresh_token"}
    #     refresh_token_update = getAccessToken(data)
    #     access_token = refresh_token_update
    #     credentials_rec.sudo().write({"wix_access_token":refresh_token_update})
    #     data={"url":STORE_ORDERS_API_URL, "access_token": refresh_token_update.get('access_token')}
    #     orders_data=getOrders(data)
    #     return  request.render('odoo_wix_connector.wix_controller', {})

    def get_instance_redirect_url(self, id):
        instance_action_id = request.env.ref('odoo_multi_channel_sale.action_multi_channel_view').id
        redirect_url = f"/web#id={id}&action={instance_action_id}&model=multi.channel.sale&view_type=form"
        return redirect_url

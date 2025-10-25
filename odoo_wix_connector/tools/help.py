# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
import requests
import json
import jwt

from logging import getLogger
_logger = getLogger(__name__)

def getTokensFromWix(data):
    url = data.pop('url')
    res=requests.request('POST', url, headers={"Content-Type":"application/json"}, data=json.dumps(data), allow_redirects=False, timeout=30)
    return res.json()

def getAccessToken(data):
    data.pop('url', False)
    res=requests.request('POST', 'https://www.wix.com/oauth/access', headers={"Content-Type":"application/json"}, data=json.dumps(data), allow_redirects=False, timeout=30)
    if res.ok:
        return res.json()
    return False

# def getInstance(data):
#     url = data.pop('url')
#     res=requests.request('GET','https://www.wixapis.com/apps/v1/instance', headers={"authorization": data.get('access_token')}, allow_redirects=False, timeout=30)
#     return res.json()

def getDefaultparameters():
    return {
        "AUTH_PROVIDER":'https://www.wix.com/oauth',
        "permissionRequestUrl":'https://www.wix.com/app-oauth-installation/consent',
        "APP_ID":'d7a7f0ca-c0fd-4e4f-97a6-de6c42ab966a',
        "APP_SECRET":'f4fbb0e1-87a6-4d4b-9dbd-6545640e088c',
        "INSTANCE_API_URL" :'https://www.wixapis.com/apps/v1'
    }

def getProducts(data):
    res=requests.request('POST',data.get("url"),data=json.dumps({}),headers={"authorization": data.get('access_token')}, allow_redirects=False, timeout=30)
    return res.json()

def getOrders(data):
    url = data.get("url")+"/orders/query"
    res=requests.request('POST',url,data=json.dumps({}),headers={"authorization": data.get('access_token')}, allow_redirects=False, timeout=30)
    return res.json()

def jwt_Token(data, instance_id):
    try:
        _logger.info('===+++ Calling Wix Webhook +++===')
        public_key = instance_id.wix_webhook_public_key
        if public_key:
            header = jwt.get_unverified_header(data.get("token"))
            algorithm = 'RS256'
            if header.get('alg'):
                algorithm  = header.get('alg')
            data_jwt=jwt.decode(data.get("token"), public_key, algorithms=[algorithm])
            try:
                final_data = json.loads(json.loads(data_jwt.get('data')).get('data'))
            except:
                _logger.info(data_jwt)
                final_data = json.loads(data_jwt.get('data'))
            return {'data':final_data}
        else:
            _logger.info(f'Error Webhook: Channel {instance_id.name} has no value in Webhook Public Key field')
    except Exception as e:
        _logger.error('Webhook: Something went wrong in Real-Time Sync Webhook %r',e, exc_info=True)
    return False
    

# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import models, api
from odoo.addons.odoo_wix_connector.tools.wix_api import Wix

class MultiChannelSale(models.Model):
    _inherit = 'multi.channel.sale'
    
    def get_core_feature_compatible_channels(self):
        return ['wix']

    @api.model
    def get_channel(self):
        channel_names = super(MultiChannelSale, self).get_channel()
        channel_names.append(('wix', 'Wix'))
        return channel_names
    
    @api.model
    def get_wix_channel_id(self):
        return self.env['multi.channel.sale.config'].sudo().get_default_fields({}).get('default_wix_channel_id')
    
    @api.model
    def get_wix_sdk(self):
        message= ''
        sdk = None
        url = 'https://www.wix.com/oauth/access'
        sdk = Wix(
                APP_ID=self.wix_app_id,
                APP_SECRET=self.wix_app_secret_key,
                base_uri=url,
                access_token= self.wix_access_token,
                grant_type= "refresh_token",
                debug=self.debug == 'enable'
            )
        return dict(
            sdk=sdk,
            message=message,
        )

    @api.model
    def get_info_urls(self):
        urls = super(MultiChannelSale,self).get_info_urls()
        urls.update(
            wix = {
                'blog' : 'https://webkul.com/blog/user-guide-for-odoo-wix-connector-for-multichannel/',
                'store': 'https://store.webkul.com/odoo-wix-connector-for-multichannel.html',
            },
        )
        return urls

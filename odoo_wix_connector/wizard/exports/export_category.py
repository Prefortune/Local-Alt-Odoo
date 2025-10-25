# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from logging import getLogger
_logger = getLogger(__name__)

from odoo import models

class ExportWixCategories(models.TransientModel):
    _inherit = "export.categories"

    def wix_update_now(self, sdk, category_id, remote_id):
        sdk = sdk.get('sdk')
        return self.update_wix_category(sdk, category_id, remote_id)
    
    def update_wix_category(self, sdk, category_id, store_id):
        data = {"name": category_id.name}
        result = sdk.update_collection(store_id, data)
        if result:
            return (True, 'Updated')
        return (False, 'Error')

    def wix_export_now(self, record, initial_record_id):
        data_list = [False, {}]
        if record.parent_id:
            _logger.error('Error: Can not export category which has a parent')
        else:
            sdk = self._context.get("wix").get('sdk')
            cat_id = self._wix_sync_categories(sdk, record)
            if cat_id:
                data_list = [True, {"id":cat_id}]
        return data_list
        

    def _wix_sync_categories(self, sdk, record):
        data={
            'collection':{
                'name':record.name
        }}
        store_id=sdk.create_collection(data)
        if store_id.get('data'):
            store_id=store_id.get('data').get('collection').get('id')
            return store_id
        else:
            _logger.info('Something Went Wrong: %r',store_id)
        return False

# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import models, _

class ImportWixCategories(models.TransientModel):
    _name = "import.wix.categories"
    _inherit = ['import.categories']
    _description = "Wix Categories import wizard"

    @staticmethod
    def wix_extract_categ_data(data,channel_id,**kwargs):
        return  dict(
            channel_id=channel_id,
            name=data.get('name'),
            store_id=data.get('id'),
            )

    def import_now(self, channel_id, sdk,kwargs):
        if kwargs.get('filter_on') == "category_id":
            fetch_res = sdk.get_collection(kwargs.get('category_id')).get('data').get('collection')
            return [self.wix_extract_categ_data(fetch_res,channel_id.id)]
        else:
            fetch_res =sdk.get_collections()
        categories = fetch_res.get('data') or {}
        kwargs.update(page_size=10000) #making it bigger for breaking pagination loop at base module
        message = fetch_res.get('message','')
        if not categories:
            message+="Category data not received."
            kwargs.update(
                message=message
            )
            return []
        else:
            categ_items=[]
            for category in categories.get("collections"):
                categ_items.append(self.wix_extract_categ_data(category,channel_id.id))
            return categ_items

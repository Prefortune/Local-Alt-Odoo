# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import api, fields, models
class ImportOperation(models.TransientModel):
    _inherit = 'import.operation'

    wix_filter_type = fields.Selection(
        selection=[
            ('all','All'),
            ('date_range','Date Range'),
            ('category_id', 'Category ID'),
            ('customer_id', 'Customer Email'),
            ('store_id', 'Store ID'),
            ('order_state', 'Order State')
        ], default = "all",
    )
    wix_start_date = fields.Datetime("From Wix Date")
    wix_end_data = fields.Datetime("Till Wix Date")
    wix_category_id = fields.Char('Category ID',help="Get product which belongs to this category ID")
    wix_customer_email = fields.Char('Customer Email', help="Get Orders made by specific customers",size=30)
    wix_order_state = fields.Selection([('PAID','Paid'),('NOT_PAID','Unpaid')])
    wix_store_id = fields.Char('Store ID', help="Get Orders")
    #more filter types to be implemented

    def wix_get_filter(self):
        kw = {'filter_on':self.wix_filter_type}
        kw['operation'] = self.operation
        if self.wix_start_date or self.wix_end_data:
            kw['start_date'] = self.wix_start_date
            kw['end_date'] = self.wix_end_data
        elif self.wix_category_id:
            kw.update(
                category_id=self.wix_category_id
            ) 
        elif self.wix_customer_email:
            kw.update(
                customer_email=self.wix_customer_email
            )
        elif self.wix_order_state:
            kw.update(
                order_state=self.wix_order_state
            )
        elif self.wix_store_id:
            kw.update(
                store_id=self.wix_store_id
            )
        return kw


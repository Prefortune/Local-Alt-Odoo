# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
# import re
from odoo import api, fields, models, _

from logging import getLogger
_logger = getLogger(__name__)

class WixChannelSale(models.Model):
    _inherit = "multi.channel.sale"
    wix_app_id = fields.Char(
        string="App ID", help='eg. d7a7f0ca-c0fd-4e4f-97a6-de6c42ab966a')
    wix_app_secret_key = fields.Char(
        string='App Secret Key', help='eg. f4fbb0e1-87a6-4d4b-9dbd-6545640e088c',)
    wix_access_token = fields.Char(string="Access token") #eg: {'access_token': '--..--', 'refresh_token': '---..--'}
    # wix_refresh_token = fields.Char(string="Refresh token")
    # instance_id = fields.Integer(string='Instance id')

    # Base URLs
    wix_base_redirectUrl = fields.Char(string="Redirect Url", default = lambda self: self.get_base_url(), help = "Please Add your Odoo URL")
    wix_redirect_url = fields.Char(string="Redirect EndPoint", compute="wix_urlchange")
    wix_app_url = fields.Char(string="App URL")

    # Webhooks configuration
    wix_webhook_public_key = fields.Text(string='Public key')
    wix_show_webhook = fields.Boolean()
    wix_order_webhook_enable = fields.Boolean()
    wix_order_webhook_url = fields.Char(
        help="Paste this URL to the New Order Webhook in Wix Application")
    wix_order_cancel_webhook_enable = fields.Boolean()
    wix_order_cancel_webhook_url = fields.Char(
        help="Paste this URL to the Order Canceled Webhook in Wix Application")
    wix_product_create_webhook_url = fields.Char(
        help="Paste this URL to the Product Created Webhook in Wix Application")
    wix_product_create_webhook_enable = fields.Boolean()

    def get_base_url(self):
        odoo_domain = self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
        return odoo_domain

    @api.depends('wix_redirect_url')
    def wix_urlchange(self):
        for record in self:
            base_url = record.wix_base_redirectUrl
            if base_url.endswith('/'):
                base_url = base_url[:-1]
                record.wix_base_redirectUrl = base_url
            record.write({
                'wix_redirect_url': base_url + "/wix/login/"+str(self.id),
                'wix_app_url': base_url + "/wix/signup/"+str(self.id),
                'wix_order_webhook_url': base_url + "/wix/order_new/"+str(self.id),
                'wix_order_cancel_webhook_url': base_url + "/wix/order_cancel/"+str(self.id),
                'wix_product_create_webhook_url':  base_url + "/wix/product_new/"+str(self.id)
            })

    def create_wix_connection(self):
        # Wix Connection button
        url = f"https://www.wix.com/installer/install?appId={self.wix_app_id}&redirectUrl={self.wix_redirect_url}"
        return {
                "type": "ir.actions.act_url",
                        'target': 'self',
                        "url": url
            }

    def connect_wix(self):
        for obj in self:
            state = False
            if not obj.wix_access_token:
                return state, "<p class='text-danger'>Wix Token not exists, please create connection again</p>"
            res = obj.get_wix_sdk()
            sdk = res.get('sdk')
            if not (sdk and sdk.oauth_token):
                message = '<br/>%s' % (res.get('message'))
                message += '<br/>Oauth Token not received.'
            else:
                self.write({"wix_access_token": sdk.oauth_token})
                state = True
                message = """<br/>
                    <p style = "color:green;">
                        Successfully Connected to Wix
                    </p>
                """
        return state, message


    # def test_wix_connection(self):
    #     for obj in self:
    #         res = obj.get_wix_sdk()
    #         sdk = res.get('sdk')
    #         if not (sdk and sdk.oauth_token):
    #             message += '<br/>%s' % (res.get('message'))
    #             message += '<br/>Oauth Token not received.'
    #         else:
    #             self.write({"wix_access_token": sdk.oauth_token})
    #             state = 'validate'
    #             message += """<br/>
    #                 <p style = "color:green;">
    #                     Successfully Connected to Wix
    #                 </p>
    #             """
    #         obj.state = state
    #         if state != 'validate':
    #             message += '<br/> Error While Credentials  validation.'
    #     return self.display_message(message)

    def write(self, vals):
        for record in self:
            if record.channel == "wix":
                if 'wix_app_id' in vals or 'wix_app_secret_key' in vals:
                    vals.update({'wix_access_token': False})
        return super(WixChannelSale, self).write(vals)

    def wix_pagination(self, kwargs, total):
        current_page = kwargs.get('current_page') if kwargs.get('current_page') else 0
        if kwargs.get('current_page')+kwargs.get('page_size') >= total and not kwargs.get('wix_next_url'):
            kwargs.update({'page_size': kwargs.get('page_size')+1})
        current_page += kwargs.get('page_size')
        kwargs.update(current_page=current_page)
        return kwargs


# --------------------------- Import Process ----------------------

    def import_wix(self, object, **kwargs):
        self.ensure_one()
        channel_id = self
        result = []
        try:
            res = channel_id.get_wix_sdk()
            sdk = res.get('sdk')
            if kwargs.get('message'):kwargs['message'] = ''
            if not (sdk and sdk.oauth_token):
                return None,None
            if object == 'product.category':
                result = self.env['import.wix.categories'].import_now(channel_id, sdk, kwargs)
            elif object == 'res.partner':
                result, kwargs = self.env['import.wix.partners'].import_now(channel_id,sdk,kwargs)
            elif object == 'product.template':
                result, kwargs = self.env['import.wix.products']._wix_import_products(sdk, channel_id, kwargs)
            elif object == 'sale.order':
                result, kwargs = self.env['import.wix.orders']._wix_import_orders(sdk,channel_id, kwargs)
            elif object == 'product.attribute':
                result = []
                kwargs.update(
                    message="For wix this operation gets automatically executed when Product Sync run, so you don't have to run it spearately."
                )
            elif object == 'delivery.carrier':
                result = []
                kwargs.update(
                    message="For wix this operation gets automatically executed when order sync run, so you don't have to run it spearately."
                )
        except Exception as e:
            _logger.error('Error: %r',e, exc_info=True)
        return result, kwargs

# ---------------------------Export Process -----------------------

    def export_wix(self, record):
        data_list = [False, {}]
        try:
            sdk = self.get_wix_sdk()
            if sdk:
                if record._name == 'product.category':
                    initial_record_id = record.id
                    data_list = self._export_wix_categories(
                        sdk, record, initial_record_id)
                elif record._name == 'product.template':
                    data_list = self._export_wix_product(
                        sdk, record)
        except Exception as e:
            _logger.error('Error: %r',e, exc_info=True)
        return data_list

    def _export_wix_categories(self, sdk, record, initial_record_id):
        obj = self.env['export.categories'].create(
            {
                'channel_id': self.id,
                'operation': 'export',
            })

        return obj.with_context({
            'wix': sdk,
            'channel_id': self,
        }).wix_export_now(record, initial_record_id)

    def _export_wix_product(self, sdk, record):
        obj = self.env['export.templates'].create(
            {
                'channel_id': self.id,
                'operation': 'export',
            }
        )
        return obj.with_context({
            'wix': sdk,
            'channel_id': self,
            'operation': 'export',
        }).wix_export_now(record)

# ------------------------Update Process -----------------------

    def update_wix(self, record, get_remote_id):
        try:
            sdk = self.get_wix_sdk()
            data_list = [False, 'Error']
            if sdk:
                remote_id = get_remote_id(record)
                if record._name == 'product.category':
                    initial_record_id = record.id
                    data_list = self._update_wix_categories(
                        sdk, record, initial_record_id, remote_id)
                elif record._name == 'product.template':
                    data_list = self._update_wix_product(
                        sdk, record, remote_id)
        except Exception as e:
            _logger.error('Error: %r',e, exc_info=True)
        return data_list

    def _update_wix_categories(self, sdk, record, initial_record_id, remote_id):
        obj = self.env['export.categories'].create(
            {
                'channel_id': self.id,
                'operation': 'update',
            }
        )
        return obj.with_context({
            'wix': sdk,
            'channel_id': self,
        }).wix_update_now(sdk, record, remote_id)

    def _update_wix_product(self, sdk, record, remote_id):
        obj = self.env['export.templates'].create(
            {
                'channel_id': self.id,
                'operation': 'update',
            }
        )
        return obj.with_context({
            'wix': sdk,
            'channel_id': self,
            'operation': 'update',
        }).wix_update_now(record, remote_id)

# ----------------------------------- Core Methods -----------------------------------------------
    
    def wix_post_do_transfer(self, stock_picking, mapping_ids, result):
        carrier_tracking = stock_picking.carrier_tracking_ref
        carrier_id = stock_picking.carrier_id.name
        sdk = self.get_wix_sdk().get('sdk')
        order_id = mapping_ids[0].store_order_id
        line_items = []
        res = sdk.get_Order(order_id)
        line_data = res.get('data').get('orders')[0].get('lineItems') if res.get('data').get('orders') else []
        for product in stock_picking.move_line_ids_without_package:
            product_id = product.product_id
            if product_id.channel_mapping_ids:
                store_product_id = product_id.channel_mapping_ids.store_product_id
                store_variant_id = product_id.channel_mapping_ids.store_variant_id
                for rec in line_data:
                    if rec.get('catalogReference').get('options', {}).get('variantId'):
                        store_id =  rec.get('catalogReference').get('options', {}).get('variantId')
                        if store_id == store_variant_id:
                            line_items.append({
                            "id":rec.get('id'),
                            "quantity":int(product.quantity),
                        })
                    else:
                        store_id =  rec.get('catalogReference').get('catalogItemId')
                        if store_id == store_product_id:
                                line_items.append({
                                "id":rec.get('id'),
                                "quantity":int(product.quantity),
                            })
            else:
                _logger.info('Product has no Mapping available')
        data = {
                "lineItems": line_items,
        }
        if carrier_tracking and carrier_id:
            data.update({"trackingInfo":{
                            "shippingProvider": carrier_id,
                            "trackingNumber":carrier_tracking
                        }})
        res = sdk.order_fullfillment(order_id, data)
        if not res:
            _logger.info('Error: Real time update shipment status to wix Not Success')
            return False
        _logger.info('Success: Real time update shipment status to Wix Success')

    def wix_post_confirm_paid(self, invoice, mapping_ids, result):
        try:
            sdk = self.get_wix_sdk().get('sdk')
            order_id = mapping_ids[0].store_order_id
            order_data = sdk.get_Order(order_id)
            if order_data.get("data"):
                amount=order_data.get('data').get('order').get('priceSummary').get('total').get('amount')
                params={
                        "payments": [
                                {
                                    "amount": {
                                        "amount": str(float(amount))
                                    },
                                    "regularPaymentDetails": {
                                        "status": "APPROVED",
                                        "paymentMethod": "Offline" # Cash, In Person etc.
                                    }
                                }
                            ],
                        }
                endpoint ='https://www.wixapis.com/ecom/v1/payments/orders/{id}/add-payment'.format(id=order_id)
                headers={"Authorization": str(sdk.oauth_token.get("access_token"))}
                res = sdk._post_data(endpoint,headers=headers,data=params,auth=True)
                if not res.get("data"):
                    _logger.info('Error: Real time update payment order status to Wix Not Success')
                    return False
                status=(mapping_ids.store_order_status).replace('NOT_PAID','PAID')
                mapping_ids.store_order_status=status
                _logger.info('Success: Real time update payment order status to Wix Success')
            else:
                _logger.info('+++++++++++Order Not Found+++++++++')
        except Exception as e:
            _logger.error(e, exc_info=True)

    def wix_post_cancel_order(self, sale_order, mapping_ids, result):
        if sale_order.state == 'cancel':
            sdk = self.get_wix_sdk().get('sdk')
            order_id = mapping_ids[0].store_order_id
            params={
                        "customMessage": "Canceled",
                        "restockAllItems": True
                    }
            endpoint ='https://www.wixapis.com/ecom/v1/orders/{id}/cancel'.format(id=order_id)
            headers={"Authorization": str(sdk.oauth_token.get("access_token"))}
            res = sdk._post_data(endpoint,headers=headers,data=params,auth=True)
            if not res.get("data"):
                _logger.info('Error: Real time update cancel order status to Wix Not Success')
                return False
            _logger.info('Success: Real time update cancel order status to Wix Success')

    def sync_quantity_wix(self, mapping, qty):
        store_id = mapping.store_product_id
        variant_qty_data = [{mapping.store_variant_id:qty}]
        self.sync_quantity_wix_data(store_id, variant_qty_data, qty=qty)

    def sync_quantity_wix_data(self, product_store_id, variant_qty_data=False, qty=False):#for simple type no need to pass variant_qty_data
        # variant_qty_data format : [{'variant_id',qty},{--}]
        sdk = self.get_wix_sdk().get('sdk')
        variants = []
        variant_qty_data=[{"No Variants":qty}] if not variant_qty_data else variant_qty_data
        for variant_id in variant_qty_data:
            store_variant_id = list(variant_id.keys())[0]
            qty = variant_id.get(store_variant_id)
            if store_variant_id == "No Variants":
                store_variant_id = "00000000-0000-0000-0000-000000000000"
            variants.append({
                "variantId": str(store_variant_id),
                "quantity": qty,
                "inStock":True,
            })
        data = {
            "inventoryItem": {
                "trackQuantity": True,
                "variants": variants
            }
        }
        res = sdk.update_quantity_realtime(data, product_store_id)
                

# ---------------------------CRON OPERATIONS ---------------------------------------

    def wix_import_order_cron(self):
        _logger.info("+++++++++++Import Order Cron Started++++++++++++")
        kw = dict(
            object="sale.order",
            page=1,
            wix_import_date_from=self.import_order_date,
            from_cron=True
        )
        self.env["import.operation"].create({"channel_id": self.id,
                                             }).import_with_filter(**kw)

    def wix_import_product_cron(self):
        _logger.info("+++++++++++Import Product Cron Started++++++++++++")
        kw = dict(
            object="product.template",
            page=1,
            wix_import_date_from=self.import_product_date,
            from_cron=True
        )
        self.env["import.operation"].create({
            "channel_id": self.id,
        }).import_with_filter(**kw)

    def wix_import_partner_cron(self):
        _logger.info("+++++++++++Import Partner Cron Started++++++++++++")
        kw = dict(
            object="res.partner",
            page=1,
            wix_import_date_from=self.import_customer_date,
            from_cron=True,
        )
        self.env["import.operation"].create({
            "channel_id": self.id,
        }).import_with_filter(**kw)

    def wix_import_category_cron(self):
        _logger.info("+++++++++++Import Category Cron Started++++++++++++")
        kw = dict(
            object="product.category",
            page=1,
            from_cron=True,
        )
        self.env["import.operation"].create({
            "channel_id": self.id,
        }).import_with_filter(**kw)
        
    # ------------------Available  Feature-------------------------
    def wix_available_configs(self):
        return [
                # Webhooks Add from extension when implemented
                # 'webhook_available', 
                # 'create_order_webhook',
                # 'update_order_webhook',
                
                # base
                # 'child_store_config',

                # Import Crons
                'cron_available',
                'import_order_cron',
                'order_created_after',
                # 'order_updated_after',
                'import_product_cron',
                'product_created_after',
                # 'product_updated_after',
                'import_partner_cron',
                'partner_created_after',
                # 'partner_updated_after',
                'import_category_cron',

                # realtime export
                'sync_order_invoice',
                'sync_order_shipment',
                'sync_order_cancel',
            ]

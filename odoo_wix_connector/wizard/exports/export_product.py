# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from urllib import parse as urlparse
from logging import getLogger
_logger = getLogger(__name__)

from odoo import models,_
from odoo.exceptions import UserError


# Need to optimize the export product(this file)
class ExportWixTemplates(models.TransientModel):
    _inherit = "export.templates"

    def wix_export_now(self, record):
        if record.type in ['product','consu']:
            remote_object = {}
            channel = self._context.get('channel_id')
            if channel.wix_product_create_webhook_enable:
                _logger.warning("Please make sure to disable Wix Product Create Webhook during export product operation from odoo")
                raise UserError(f"Please disable the Product Create Webhook for {channel.channel} channel")
            sdk = self._context.get('wix').get('sdk')
            # categ_ids = self._set_wix_product_categories(sdk, channel, record)
            response_id, variant_list = self._wix_export_update_template(sdk, channel, record)
            if response_id:
                self.add_product_category(sdk, channel,record,response_id)# add category
                remote_object["id"]=response_id
                if remote_object['id']:
                    remote_object["variants"] = [{"id": variant_id} for variant_id in variant_list]
                    return True, remote_object
        else:
            # Currently, only creating physical products ( "productType": "physical" ) is supported via the API.
            _logger.info('The wix connector does not export service type of products: %r', record.name)
        return False,False
    
    def wix_update_now(self, record, remote_id):
        channel = self._context.get('channel_id')
        sdk = self._context.get('wix').get('sdk')
        mapping_id = channel._match_mapping(self.env['channel.template.mappings'],domain =[('template_name','=',record.id)],limit=1)
        if mapping_id:# Reset all variants of the product first
            sdk.reset_product_variants(mapping_id.store_product_id)
        id, variant_list = self._wix_export_update_template(sdk, channel, record)
        if id:
            self.add_product_category(sdk, channel, record, id) # add category
            return [True, "Updated"]
        return [False, 'Error']

    def get_product_basic_vals(self, channel, template, manage_variants=False):
        return {
            'name'				: template.name,
            "productType"       : "physical",
            "priceData"         : {
            "price"             : float(channel.pricelist_name._get_product_price(template, quantity=1))    
                                    },
            "manageVariants" 	: manage_variants,
            'description'		: template.description_sale or "",
            'weight'            :float(template.weight),
        }

    def _wix_export_update_template(self, sdk, channel, template_record):
        data_list=[False, False]
        returnid = False
        channel = self._context.get('channel_id')
        if template_record.attribute_line_ids:
            returnid, variant_list = self._create_update_wix_variable_product(
                sdk, channel, template_record)
            data_list = [returnid, variant_list]
        else:
            if not template_record.default_code:
                template_record.default_code = channel.sku_sequence_id.next_by_id() if channel.sku_sequence_id else False
                if not template_record.default_code:
                    _logger.info(f'== Please Add SKU/Internal Reference to the product [{template_record.name}]')
                    return data_list
            returnid = self._create_update_wix_simple_product(
                sdk, channel, template_record)
            data_list = [returnid, ["No Variants"]]
        if returnid:
            if self._context.get('operation') == "export":
                #add image/media only the time of export because it can not replace image
                self.add_product_image(sdk, returnid, template_record)
        return data_list

    def add_product_image(self,sdk, remote_id, template):
        product_id = template.product_variant_id
        url = False
        if product_id.image_1920:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            name = product_id.name.replace(' ', '-').replace('/','-')
            image_url = f"/channel/image/product.product/{product_id.id}/image_1920/{name}.png"
            url = urlparse.urljoin(base_url, image_url)
        if url:
            sdk.add_product_media(remote_id, url)

    def _create_update_wix_variable_product(self, sdk, channel, template):
        # Check if there is no sku for any of the variants
        if False in template.product_variant_ids.mapped('default_code'):
            if channel.sku_sequence_id: # crating sku if SKU Pattern setup in channel configuration
                for product_var in template.product_variant_ids.filtered(lambda x: x.default_code == False):
                    product_var.default_code = channel.sku_sequence_id.next_by_id()
            else:
                _logger.info(f'Error: Please Add SKU/Internal Reference to all variant of the product [{template.name}]')
                return [],[]
        attribute_list = [{
            'name':att.attribute_id.name, 
            'choices':[
                {'value': name, 'description': name} for name in att.value_ids.mapped('name')]
        } for att in template.attribute_line_ids]
        # attribute_list = []
        # for att in template.attribute_line_ids:
            # choices = [{'value':name, 'description':name} for name in att.value_ids.mapped('name')]
            # attribute_list.append(
            #     {
            #         'name':att.attribute_id.name,
            #         'choices': choices
            #     })
        # attribute_value_ids = template.mapped('product_variant_ids').mapped('product_template_attribute_value_ids')
        # attribute_list=[]
        # attribute_option={}
        # for product in template.product_variant_ids:
        #     if not product.default_code:
        #         product.default_code = channel.sku_sequence_id.next_by_id() if channel.sku_sequence_id else False
        #         if not product.default_code:
        #             _logger.info(f'== Please Add SKU/Internal Reference to the product [{product.name}]')
        #             return [],[]
        # for attribute_value_id in attribute_value_ids:
        #     attribute_id = attribute_value_id.attribute_id
        #     if attribute_id.name in attribute_option:
        #         attri_options=attribute_option.pop(attribute_id.name)
        #         attri_options.append(attribute_value_id.name)
        #         attribute_option.update({attribute_id.name:attri_options})
        #     else:
        #         attribute_option.update({attribute_id.name:[attribute_value_id.name]})
        # for atribute in attribute_option:
        #     attribute_dict={}
        #     attribute_dict.update({'name':atribute})
        #     choices=[]
        #     for attribute_value in  attribute_option.get(atribute):
        #         attribute_choice={}
        #         attribute_choice.update({"value":attribute_value,"description":attribute_value})
        #         choices.append(attribute_choice)
        #     attribute_dict.update({"choices":choices})
        #     attribute_list.append(attribute_dict)
        productDict = self.get_product_basic_vals(channel, template, manage_variants=True)
        productDict["productOptions"] = attribute_list
        if self._context.get('operation') == "export":
            returnDict = sdk.create_product(productDict)
            if not returnDict.get('data'):
                _logger.info('Error in export product sku [%r] Error: %r',template.default_code, returnDict)
                return [],[]
            storeTemplateId = returnDict.get("data").get('product').get('id')
            returnList=[]
            variants = returnDict.get("data").get('product').get('variants')
            quant_data = {
            "inventoryItem": {
                    "trackQuantity": True,
                    }
            }
            var_quant_data = []
            for product_id in template.product_variant_ids:
                # attributes_option ={}
                # for attribute_value_id in product_id.product_template_attribute_value_ids:
                #     attributes_option.update({attribute_value_id.attribute_id.name: attribute_value_id.name})
                attributes_option = {
                    attribute_value_id.attribute_id.name: attribute_value_id.name for attribute_value_id in product_id.product_template_attribute_value_ids}
                for variant in variants:
                    # Matching choices(attributes) of the variants and response
                    if variant.get('choices') ==  attributes_option:
                        returnList.append(variant.get('id'))
                        if quant_data.get('inventoryItem').get('variants'):
                            if variant.get('id') == quant_data.get('inventoryItem').get('variants')[-1].get('variantId'):
                                break
                        var_quant_data.append({
                                "variantId": variant['id'],
                                "quantity": int(product_id.qty_available),
                                "inStock":True,
                            })# Adding Quantity for this variant by calling another api
                        quant_data['inventoryItem'].update({'variants':var_quant_data})
                        break # if match choices then exits from inner loop
            if quant_data.get('inventoryItem').get('variants'):
                res = sdk.update_quantity_realtime(quant_data, storeTemplateId)
            res = self.update_product_variants(sdk, channel, template, productDict, id = storeTemplateId)
            return storeTemplateId, returnList
        elif self._context.get('operation') == "update":
            res = self.update_product_variants(sdk, channel, template, productDict)
            return res
        return [],[]

    # We need to update variants after we export them using export operation itself
    def update_product_variants(self, sdk, channel, template, productDict , id = False):
        product_mapped = self.env["channel.template.mappings"].search([
            ("channel_id","=",channel.id),
            ("odoo_template_id","=",template.id)
            ])
        if id: # During Export operation
            return self.update_variant_data(sdk, channel, template, id)
        if product_mapped: # During Update operation
            ID=product_mapped.store_product_id
            sdk.update_product(Id=ID,data=productDict) # Update the template at wix end
            return self.update_variant_data(sdk, channel, template, ID) # update variants data

    def update_variant_data(self, sdk, channel, template, ID):
        product_list=[]
        product_variant_ids = template.product_variant_ids
        created_ids = []
        ProductMappingIds = self.remove_inactive_product_mappings(channel, template)
        for product_id in product_variant_ids:
            # if self._context.get('operation')=="update":
            #     matchRecord = ProductMappingIds.filtered(lambda x: x.product_name == product_id)
            #     if not matchRecord:
            #         created_ids.append(product_id)
            attributes_option ={}
            choices={}
            for attribute_value_id in product_id.product_template_variant_value_ids:
                choices.update({attribute_value_id.attribute_id.name: attribute_value_id.name})
            attributes_option.update({
                "choices":choices,
                "price": float(channel.pricelist_name._get_product_price(product_id, quantity=1)),
                "weight":product_id.weight,
                "sku":product_id.default_code
                })
            product_list.append(attributes_option)
        prod_data={
            "variants":  product_list
        }
        returnDict=sdk.update_variant_product(Id=ID,data=prod_data) # Update product variants
        if returnDict.get('data').get('variants'):
            if self._context.get('operation')=="update":
                self.create_updated_product_variants_mappings(channel, returnDict, template, ID, product_variant_ids,created_ids)
            return [ID, returnDict.get('data').get('variants')]
        return [False, 'Error']

    def create_updated_product_variants_mappings(self,channel, data, template, store_id,variant_ids,created_ids):
        variant_id = False
        variant_qty_data = []
        if data.get('data').get('variants'):#Update qty of product after exporting(also in export operation itself)
            for varient in data.get('data').get('variants'):
                variant_id = variant_ids.filtered(lambda x: x.default_code == varient.get('variant').get('sku'))
                if variant_id:
                    variant_id = variant_id[0]
                    variant_qty_data.append({varient.get('id'): channel.get_quantity(variant_id)})
                if not channel.match_product_mappings(store_id, varient.get('id')):
                    match_variant = channel.match_product_mappings(store_id, domain=[('product_name','=',variant_id.id)])
                    # match by variant product in mapping
                    if match_variant: # If store variant_id is changed after update
                        match_variant.unlink() # unlink previous mapping
                    # if variant_id in created_ids:
                    channel.create_product_mapping(template, variant_id,
                            store_id, varient.get('id'), vals={'default_code':variant_id.default_code})
            channel.sync_quantity_wix_data(store_id, variant_qty_data) # Adding variants quantity
        return True

    def _create_update_wix_simple_product(self, sdk, channel, template):#Create/update simple type products:
        returnDict=[]
        operation = self._context.get('operation')
        productDict = self.get_product_basic_vals(channel, template)
        productDict['sku'] = template.default_code
        if operation == "export":
            returnDict=sdk.create_product(productDict)
        elif operation == "update":
            returnDict = self.update_wix_simple_product(channel, sdk, template, productDict)
        if returnDict.get('data'):
            p_id = returnDict.get('data').get('product').get('id')
            if p_id:
                channel.sync_quantity_wix_data(p_id, qty = channel.get_quantity(template))
            return returnDict.get('data').get('product').get('id')
        else:
            _logger.info(f'Error in {operation} product sku {template.default_code}')
            return False

    def update_wix_simple_product(self,channel, sdk, template, productDict):
        returnDict={}
        variant_id = template.product_variant_id
        product_mapped = self.env["channel.template.mappings"].search([
                ("channel_id","=",channel.id),
                ("odoo_template_id","=",template.id)
                ],limit = 1)
        if product_mapped:
            ID=product_mapped.store_product_id
            returnDict=sdk.update_product(Id=ID,data=productDict)
            if returnDict.get('data').get('product'):
                ProductMappingIds= self.remove_inactive_product_mappings(channel, template)
                matchRecord = ProductMappingIds.filtered(lambda x: x.product_name == variant_id)
                if not matchRecord:
                    channel.create_product_mapping(template, variant_id,
                        ID, "No Variants", vals={'default_code':template.default_code,'store_variant_id':False})
        return returnDict

    def remove_inactive_product_mappings(self,channel, template_id):
        ProductMappingIds = self.env["channel.product.mappings"].search([
            ("channel_id", "=", channel.id),
            ("odoo_template_id", "=", template_id.id)
        ])
        if self._context.get('operation') == "update":
            product_variant_ids = template_id.product_variant_ids
            if len(ProductMappingIds) >= len(product_variant_ids) and self._context.get('operation') == "update":
                inactive_product_mapping_ids = ProductMappingIds.filtered(lambda map:map.product_name not in product_variant_ids)
                inactive_product_mapping_ids.unlink()
                ProductMappingIds = ProductMappingIds - inactive_product_mapping_ids
        return ProductMappingIds
    
    def add_product_category(self, sdk, channel,record,product_store_id):
        categ_list = self._set_wix_product_categories(sdk, channel, record)
        if categ_list:
            for categ_store_id in categ_list:# It will only append product inside collection not remove/replace
                if not categ_store_id == "00000000-000000-000000-000000000001": # No need to add this default category is always added bydefault 
                    sdk.add_product_to_collection(product_store_id, categ_store_id)

    def _set_wix_product_categories(self, sdk, channel, template):
        categ_list = []
        for extra_categ in template.channel_category_ids:
            if extra_categ.instance_id.id == channel.id:
                categ_list = list(map(lambda ele:ele, extra_categ.mapped('extra_category_ids.channel_mapping_ids.store_category_id')))
                break
        return categ_list

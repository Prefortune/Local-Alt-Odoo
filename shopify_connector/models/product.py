from odoo import api, fields, models, _
from collections import defaultdict
import base64
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class ShopifyProductTemplate(models.Model):
    _inherit = "product.template"

    shopify_product_id = fields.Char(string="Shopify Product Id")
    shopify_store = fields.Many2one('shopify.connector', string="Shopify Store")
    is_shopify_product = fields.Boolean(string="Shopify Product")

    @api.constrains('shopify_product_id', 'shopify_store')
    def _check_shopify_product_id_and_store(self):
        for record in self:
            if record.is_shopify_product and not record.shopify_store:
                raise ValidationError("You select Shopify Product, but Shopify Store is not selected.")

    @api.model_create_multi
    def create(self, vals_list): 
        temp_id = super(ShopifyProductTemplate, self).create(vals_list)
        shopify_store_value = vals_list[0].get('shopify_store')
        
        if shopify_store_value is not False and shopify_store_value is not None:
            _logger.info("create shopify %s", vals_list)
            shopify_product = self.env['shopify.product']
            shopify_create = shopify_product.post_product(vals_list[0], temp_id, shopify_store_value)
        return temp_id
    
    @api.model
    def write(self, values):
        context = self._context
        # model_value = context['params']['model']
        # model_value = context.get('params', {}).get('model', False)
        result = super(ShopifyProductTemplate, self).write(values)
        if self.is_shopify_product:
            if self.shopify_store:
                if self.shopify_store is not None and self.shopify_store is not False and 'shopify_product_id' not in values and 'def_name' not in context:
                    _logger.info("Write shopify %s", values)
                    temp_id = self
                    shopify_product = self.env['shopify.product']
                    shopify_write = shopify_product.put_product(values, temp_id, temp_id.shopify_store)
            else:
                raise ValidationError("You select Shopify Product, but Shopify Store is not selected.")
        return result


class ShopifyProductProduct(models.Model):
    _inherit = "product.product"

    shopify_product_id = fields.Char(string="Shopify Product Id")
    shopify_variant_id = fields.Char(string="Shopify Product Variant Id")
    shopify_store = fields.Many2one('shopify.connector', string="Shopify Store")
    custom_price_extra = fields.Float(string="Extra price",help="This extra price will be get from external source")

    # Override the method
    @api.depends("product_template_attribute_value_ids.price_extra")
    def _compute_product_price_extra(self):
        for product in self:
            # Your custom logic for calculating price_extra
            product.price_extra = product.custom_price_extra
            # You can modify this logic as per your requirements


class WooCommerceProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product_template_id = vals.get('product_tmpl_id')
            product_template = self.env['product.template'].browse(product_template_id)
            shopify_product = product_template.is_shopify_product
            product_variant_id = vals.get('product_id')
            product_variant = self.env['product.pricelist.item'].search([('product_id', '=', product_variant_id)])

            if shopify_product and product_variant:
                raise ValidationError("Only one Extra Price Allowed for your Shopify product, You Can update Price")
        result = super(WooCommerceProductPricelistItem, self).create(vals_list)
        return result
    
    def write(self, values):
        content = self._context
        product_template_id = self.product_tmpl_id
        shopify_product = product_template_id.is_shopify_product
        if shopify_product and 'active_model' in content:
            shopify_store = product_template_id.shopify_store
            shopify_connection = shopify_store.test_shopify_connection()
            if shopify_connection == "Connection success":
                product_variant_id = self.product_id
                shopify_product = self.env['shopify.product']
                shopify_variant_price = shopify_product._shopify_variant_price_update(product_variant_id, values, shopify_store)
        return super(WooCommerceProductPricelistItem, self).write(values)
    
class SaleOrderDiscountInherit(models.TransientModel):
    _inherit = 'sale.order.discount'


    def _create_discount_lines(self):
        """Create SOline(s) according to wizard configuration"""
        self.ensure_one()
        discount_product = self._get_discount_product()
        _logger.info("_create_discount_lines")
        if self.discount_type == 'amount':
            total_price_per_tax_groups = defaultdict(float)
            for line in self.sale_order_id.order_line:
                if not line.product_uom_qty or not line.price_unit:
                    continue

                total_price_per_tax_groups[line.tax_id] += line.price_subtotal
            if len(total_price_per_tax_groups) == 1:
                taxes = next(iter(total_price_per_tax_groups.keys()))
            else:
                taxes = self.env['account.tax']
            vals_list = [
                self._prepare_discount_line_values(
                    product=discount_product,
                    amount=self.discount_amount,
                    taxes=taxes,
                )
            ]
        else: # so_discount
            total_price_per_tax_groups = defaultdict(float)
            for line in self.sale_order_id.order_line:
                if not line.product_uom_qty or not line.price_unit:
                    continue

                total_price_per_tax_groups[line.tax_id] += line.price_subtotal

            if not total_price_per_tax_groups:
                # No valid lines on which the discount can be applied
                return
            elif len(total_price_per_tax_groups) == 1:
                # No taxes, or all lines have the exact same taxes
                taxes = next(iter(total_price_per_tax_groups.keys()))
                subtotal = total_price_per_tax_groups[taxes]
                vals_list = [{
                    **self._prepare_discount_line_values(
                        product=discount_product,
                        amount=subtotal * self.discount_percentage,
                        taxes=taxes,
                        description=_(
                            "Discount: %(percent)s%%",
                            percent=self.discount_percentage*100
                        ),
                    ),
                }]
            else:
                vals_list = [
                    self._prepare_discount_line_values(
                        product=discount_product,
                        amount=subtotal * self.discount_percentage,
                        taxes=taxes,
                        description=_(
                            "Discount: %(percent)s%%"
                            "- On products with the following taxes %(taxes)s",
                            percent=self.discount_percentage*100,
                            taxes=", ".join(taxes.mapped('name'))
                        ),
                    ) for taxes, subtotal in total_price_per_tax_groups.items()
                ]
        return self.env['sale.order.line'].create(vals_list)
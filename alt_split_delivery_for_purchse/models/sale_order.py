from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    alt_split_delivery_count = fields.Integer(string='כמות משלוחים', default=1)
    alt_split_delivery_note = fields.Char(string="הערה למשלוח", readonly=True)
    alt_split_delivery_total_price = fields.Monetary(string='עלות משלוחים כוללת', default=0.0, currency_field='currency_id')
    alt_split_delivery_url = fields.Char(string='Delivey Url', compute='_compute_alt_split_delivery_url')
    customer_delivery_date = fields.Date(string="Customer Expacted Delivery Date")
    greeting_card = fields.Text(string="Greeting Card")
    delivery_note = fields.Text(string="Delivery Note")
    
    
    def _compute_alt_split_delivery_url(self):
        for order in self:
            order.alt_split_delivery_url = f"/my/orders/{order.id}/split_delivery"

    @api.onchange('alt_split_delivery_count')
    def _OnChangeSplitCount(self):
        _logger.info("----------------_OnChangeSplitCount----------- called")
        for res in self:
            carrier_id = self.carrier_id
            split_count = res.alt_split_delivery_count
            carrier_fixed_price = carrier_id.fixed_price
            carrier_free_over = carrier_id.free_over
            carrier_free_over_amount = carrier_id.amount
            sale_order_total = sum(line.price_total for line in self.order_line if not line.is_delivery)
            support_split = carrier_id.supports_split_delivery
            _logger.info("Split Count: %s| Delivery Price: %s| Order Total: %s | Free Over: %s | Free Limit: %s", split_count, carrier_fixed_price, sale_order_total, carrier_free_over, carrier_free_over_amount)
            if self.order_line and not self.website_id and carrier_free_over and sale_order_total >= carrier_free_over_amount:
                delivery_product = carrier_id.product_id
                for line in self.order_line.filtered(lambda x : x.product_id == delivery_product and x.product_type == 'service'):
                    if split_count > 1:
                        split_count = res.alt_split_delivery_count
                        line.product_uom_qty = 1
                        line.price_unit = (split_count - 1) * carrier_fixed_price 
                        # line.price_unit = (split_count - 1) * carrier_fixed_price / split_count
                        res.alt_split_delivery_total_price = (split_count - 1) * carrier_fixed_price
                        line.name = 'Free Delivery - (1), Split Delivery'
                        _logger.info("line name ------------ %s",line.name)
                        _logger.info("Updated delivery line: Qty=%s, Unit Price=%s", line.product_uom_qty, line.price_unit)
                    else:
                        # One delivery: fully free
                        line.product_uom_qty = 1
                        line.price_unit = 0.0
                        _logger.info("Single delivery, set price 0")

    def action_confirm(self):
        res = super(SaleOrder,self).action_confirm()

        carrier_id = self.carrier_id
        carrier_free_over = carrier_id.free_over
        carrier_free_over_amount = carrier_id.amount
        support_split = carrier_id.supports_split_delivery
        sale_order_total = sum(line.price_total for line in self.order_line if not line.is_delivery)
        _logger.info("carrier_id: %s| carrier_free_over: %s| carrier_free_over_amount: %s | support_split: %s | sale_order_total: %s", carrier_id, carrier_free_over, carrier_free_over_amount, support_split, sale_order_total)

        if self.order_line and not self.website_id and not sale_order_total >= carrier_free_over_amount:
            if carrier_id and support_split:
                delivery_product = carrier_id.product_id
                for line in self.order_line.filtered(lambda x : x.product_id == delivery_product and x.product_type == 'service'):
                    _logger.info(" 88888888888888 ORDER LINES IS SERVICE %s",line.name)
                    qty = line.product_uom_qty
                    price = line.price_unit
                    self.alt_split_delivery_count = qty
                    self.alt_split_delivery_total_price = price * qty

        if self.alt_split_delivery_count > 1 and carrier_id:
            if support_split:
                _logger.info("carrier_id for order %s , %s",carrier_id.name,self.name)
                delivery_product = carrier_id.product_id
                for line in self.order_line.filtered(lambda x : x.product_id == delivery_product and x.product_type == 'service'):
                    line.name = f'{line.name} - ({self.alt_split_delivery_count})'
        return res 


    # def _compute_amounts(self):
    #     """עדכון הסכומים של ההזמנה כולל משלוחים מפוצלים"""
    #     for order in self:
    #         try:
    #             # חשב את הסכום הכולל של שורות ההזמנה
    #             amount_untaxed = sum(order.order_line.filtered(lambda l: not l.is_delivery).mapped('price_subtotal'))
                
    #             # חשב מסים
    #             amount_tax = sum(order.order_line.filtered(lambda l: not l.is_delivery).mapped('price_tax'))
                
    #             # הוסף את עלות המשלוחים המפוצלים
    #             amount_delivery = order.alt_split_delivery_total_price or 0.0
                
    #             # עדכן את השדות
    #             order.amount_untaxed = amount_untaxed
    #             order.amount_tax = amount_tax
    #             order.amount_total = amount_untaxed + amount_tax + amount_delivery
                
    #         except Exception as e:
    #             # אם יש שגיאה, השתמש בערכים ברירת מחדל
    #             order.amount_untaxed = sum(order.order_line.filtered(lambda l: not l.is_delivery).mapped('price_subtotal'))
    #             order.amount_tax = 0.0
    #             order.amount_total = order.amount_untaxed + (order.alt_split_delivery_total_price or 0.0)
                
    #     return True
    

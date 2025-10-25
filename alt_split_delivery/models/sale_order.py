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

    def action_confirm(self):
        res = super(SaleOrder,self).action_confirm()

        carrier_id = self.carrier_id
        support_split = carrier_id.supports_split_delivery

        if self.order_line and not self.website_id:
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
    
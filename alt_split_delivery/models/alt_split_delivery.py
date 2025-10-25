from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AltSplitDeliveryLine(models.Model):
    _name = 'alt.split.delivery.line'
    _description = 'Alt Split Delivery Line'
    _rec_name = 'order_line_id'

    split_delivery_id = fields.Many2one('alt.split.delivery', string='Split Delivery', required=True, ondelete='cascade')
    order_line_id = fields.Many2one('sale.order.line', string='Order Line', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    
    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than 0'))
            if record.order_line_id and record.quantity > record.order_line_id.product_uom_qty:
                raise ValidationError(_('Quantity cannot exceed order line quantity'))


class AltSplitDelivery(models.Model):
    _name = 'alt.split.delivery'
    _description = 'Alt Split Delivery'
    _rec_name = 'alt_delivery_index'
    _order = 'alt_delivery_index'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True, ondelete='cascade')
    alt_delivery_index = fields.Integer(string='Delivery Index', required=True, default=1)
    
    alt_partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', required=True)
    
    alt_delivery_price = fields.Monetary(string='Delivery Price', default=0.0, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='sale_order_id.currency_id')
    
    alt_delivery_line_ids = fields.One2many('alt.split.delivery.line', 'split_delivery_id', string='Delivery Lines')
    
    alt_delivery_notes = fields.Text(string='Delivery Notes')
    
    alt_state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True)
    
    # תאריכים
    alt_scheduled_date = fields.Datetime(string='Scheduled Date')
    alt_actual_delivery_date = fields.Datetime(string='Actual Delivery Date')
    
    # מספר משלוח
    alt_delivery_carrier_id = fields.Many2one('delivery.carrier', string='Delivery Method', help='The delivery method for this split delivery')
    
    @api.constrains('alt_delivery_index')
    def _check_delivery_index(self):
        for record in self:
            if record.alt_delivery_index <= 0:
                raise ValidationError(_('Delivery index must be greater than 0'))
    
    @api.constrains('alt_delivery_price')
    def _check_delivery_price(self):
        for record in self:
            if record.alt_delivery_price < 0:
                raise ValidationError(_('Delivery price cannot be negative'))
    
    def action_confirm(self):
        self.write({'alt_state': 'confirmed'})
    
    def action_in_transit(self):
        self.write({'alt_state': 'in_transit'})
    
    def action_delivered(self):
        self.write({
            'alt_state': 'delivered',
            'alt_actual_delivery_date': fields.Datetime.now()
        })
    
    def action_cancel(self):
        self.write({'alt_state': 'cancelled'})
    
    def name_get(self):
        result = []
        for record in self:
            name = f"Delivery {record.alt_delivery_index}"
            if record.alt_partner_shipping_id:
                name += f" - {record.alt_partner_shipping_id.display_name}"
            result.append((record.id, name))
        return result 
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AltPurchaseSplitDelivery(models.Model):
    _name = 'alt.purchase.split.delivery'
    _description = 'Alt Purchase Split Delivery'
    _rec_name = 'alt_delivery_index'
    _order = 'alt_delivery_index'

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True, ondelete='cascade')
    alt_delivery_index = fields.Integer(string='מנה מספר', required=True, default=1)
    
    # קישור ל-stock.picking הקיים
    picking_id = fields.Many2one('stock.picking', string='Delivery Picking', required=True)
    
    # הערות למנה
    alt_delivery_notes = fields.Text(string='הערות למנה')
    
    # תאריך משלוח צפוי
    alt_scheduled_date = fields.Datetime(string='תאריך משלוח צפוי')
    
    @api.constrains('alt_delivery_index')
    def _check_delivery_index(self):
        for record in self:
            if record.alt_delivery_index <= 0:
                raise ValidationError(_('Delivery index must be greater than 0'))
    
    def name_get(self):
        result = []
        for record in self:
            name = f"מנה {record.alt_delivery_index}"
            if record.purchase_order_id:
                name += f" - {record.purchase_order_id.name}"
            result.append((record.id, name))
        return result

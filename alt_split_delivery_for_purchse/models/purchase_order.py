from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # מספר המנות המבוקש
    alt_split_delivery_count = fields.Integer(string='מספר מנות', default=1)
    
    # תאריך משלוח צפוי מהספק
    supplier_delivery_date = fields.Date(string="תאריך משלוח צפוי מהספק")
    
    # כל המנות של ההזמנה
    alt_split_delivery_ids = fields.One2many(
        'alt.purchase.split.delivery', 
        'purchase_order_id', 
        string='מנות משלוח'
    )
    
    def action_create_split_deliveries(self):
        """יצירת מנות משלוח - נשתמש ב-stock.picking הקיים"""
        self.ensure_one()
        
        # מחיקת מנות קיימות
        self.alt_split_delivery_ids.unlink()
        
        # מחיקת pickings קיימים של המנות
        existing_pickings = self.picking_ids.filtered(lambda p: 'מנה' in (p.origin or ''))
        existing_pickings.sudo().unlink()
        
        # יצירת stock.picking חדש לכל מנה
        warehouse = self.warehouse_id or self.env['stock.warehouse'].search([], limit=1)
        
        for i in range(1, self.alt_split_delivery_count + 1):
            # יצירת picking חדש
            picking = self.env['stock.picking'].create({
                'partner_id': self.partner_id.id,
                'picking_type_id': warehouse.in_type_id.id,  # Incoming
                'location_id': self.partner_id.property_stock_supplier.id,
                'location_dest_id': warehouse.lot_stock_id.id,
                'origin': f"{self.name} - מנה {i}",
                'purchase_id': self.id,
            })
            
            # יצירת רשומת ניהול המנה
            self.env['alt.purchase.split.delivery'].create({
                'purchase_order_id': self.id,
                'alt_delivery_index': i,
                'picking_id': picking.id,
            })
            
        _logger.info(f"Created {self.alt_split_delivery_count} split deliveries for purchase order {self.name}")

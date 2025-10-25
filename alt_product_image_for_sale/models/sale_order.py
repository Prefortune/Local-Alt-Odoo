from email.policy import default
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    greeting_status = fields.Selection([('empty','Empty'),('not_printed','Not printed'),('printed','Printed')],compute="_compute_greeting_status",string="Greeting Status",default="empty",store=True)
    picking_status =  fields.Selection([('not_printed','Not printed'),('printed','Printed')],string="Picking Status",default="not_printed")
    # שדה לוגו לכרטיס ברכה
    logo_for_greeting_card = fields.Binary(string="לוגו לכרטיס ברכה", help="לוגו שיוצג בכרטיס הברכה")
    
    # שדה תמונת רקע לכרטיס ברכה
    background_image_greeting_card = fields.Binary(string="תמונת רקע לכרטיס ברכה", help="תמונת רקע שיוצגה בכרטיס הברכה")


    @api.depends('greeting_card')
    def _compute_greeting_status(self):
        for res in self:
            if not res.greeting_card:
                res.greeting_status = 'empty'
            else:
                res.greeting_status = 'not_printed'

    def action_print_pick_report(self):
        """Print pick report for sale order"""
        _logger.info(f"Printing pick report for orders: {self.ids}")
        
        # Add log message to chatter
        for record in self:
            try:
                record.message_post(
                    body="ההזמנה הודפסה לליקוט",
                    message_type='comment',
                    subject="הדפסת דוח ליקוט"
                )
                record.picking_status = 'printed'
                _logger.info(f"Added chatter message for order {record.name}")
            except Exception as e:
                _logger.error(f"Error adding chatter message: {e}")
        
        return self.env.ref('alt_product_image_for_sale.action_report_picking_card').report_action(self)

    def action_print_greeting_card(self):
        """Print greeting card report for sale order"""
        _logger.info(f"Printing greeting card for orders: {self.ids}")
        
        # Add log message to chatter
        for record in self:
            try:
                record.message_post(
                    body="כרטיס הברכה הודפס",
                    message_type='comment',
                    subject="הדפסת כרטיס ברכה"
                )
                record.greeting_status = 'printed'
                _logger.info(f"Added chatter message for greeting card {record.name}")
            except Exception as e:
                _logger.error(f"Error adding chatter message: {e}")
        
        return self.env.ref('alt_product_image_for_sale.action_report_greeting_card').report_action(self) 
    
    
    



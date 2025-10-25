from odoo import models, fields, api
import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # ========================================
    # שדות חדשים - סנכרון פריורטי
    # ========================================
    
    # שדות סטטוס סנכרון
    engini_sync_status = fields.Selection([
        ('pending', 'ממתין לסנכרון'),
        ('synced', 'מסונכרן'),
        ('failed', 'שגיאה בסנכרון'),
        ('not_synced', 'לא מסונכרן')
    ], string='סטטוס סנכרון', default='not_synced', tracking=True)
    
    # שדה בוליאני לחסימת סנכרון
    engini_no_sync = fields.Boolean(string='לא לסנכרון', default=False, tracking=True, 
                                   help='אם מסומן, ההזמנה לא תצא לסנכרון לפריורטי')
    
    engini_sync_date = fields.Datetime(string='תאריך סנכרון אחרון', readonly=True)
    engini_error_message = fields.Text(string='הודעת שגיאה', readonly=True)
    engini_retry_count = fields.Integer(string='מספר ניסיונות', default=0)
    engini_last_retry = fields.Datetime(string='ניסיון אחרון')
    
    # שדות מידע נוסף
    engini_customer_notes = fields.Text(string='הערות לקוח')
    engini_internal_notes = fields.Text(string='הערות פנימיות')
    engini_priority = fields.Selection([
        ('low', 'נמוך'),
        ('medium', 'בינוני'),
        ('high', 'גבוה'),
        ('urgent', 'דחוף')
    ], string='עדיפות', default='medium')
    
    # שדות חישוב
    engini_total_items = fields.Integer(string='סה"כ פריטים', compute='_compute_total_items', store=True)
    engini_has_discount = fields.Boolean(string='יש הנחה', compute='_compute_has_discount', store=True)
    
    # קשר להיסטוריית סנכרון
    engini_sync_history_ids = fields.One2many('engini.sync.history', 'order_id', string='היסטוריית סנכרון')
    engini_sync_history_count = fields.Integer(string='מספר סנכרונים', compute='_compute_sync_history_count')

    def _prepare_webhook_data(self):
        """הכנת נתוני הוובהוק - JSON עם כל פרטי ההזמנה"""
        webhook_data = {
            'order_id': self.id,
            'name': self.name,
            'date_order': self.date_order.strftime('%Y-%m-%d %H:%M:%S'),
            'partner': {
                'name': self.partner_id.display_name,
                'phone': self.partner_id.phone,
                'mobile': self.partner_id.mobile,
                'email': self.partner_id.email,
                'vat': self.partner_id.vat or '',
                'priority_customer_id': self.partner_id.ref or '',
                'street': self.partner_id.street,
                'street2': self.partner_id.street2,
                'city': self.partner_id.city,
                'zip': self.partner_id.zip,
                'state_id': self.partner_id.state_id.name if self.partner_id.state_id else False,
                'country_id': self.partner_id.country_id.name if self.partner_id.country_id else False,
            },
            'amount_total': self.amount_total,
            'lines': [],
        }
        
        # Process order lines
        for line in self.order_line:
            if not line.display_type:  # רק שורות מוצר (False = Product line)
                line_data = {
                    'product': line.product_id.name,
                    'default_code': line.product_id.default_code,
                    'quantity': line.product_uom_qty,
                    'price_total': line.price_total,
                }
                
                # Special handling for discount product (default_code 270002)
                if line.product_id.default_code == '270002':
                    line_data['quantity'] = -1
                    line_data['price_unit'] = abs(line.price_unit)  # Make sure price is positive
                
                webhook_data['lines'].append(line_data)

        payments = []
        if self.invoice_ids:
            for invoice in self.invoice_ids:
                for payment in invoice.payment_ids:
                    if payment.state == 'posted':
                        payments.append({
                            'name': payment.name,
                            'amount': payment.amount,
                            'date': payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else False,
                            'method': payment.payment_method_id.name if payment.payment_method_id else False,
                            'journal': payment.journal_id.name if payment.journal_id else False,
                            'state': payment.state,
                            'type': payment.payment_type,
                        })
            if payments:
                webhook_data['payments'] = payments
        else:
            _logger.info(f"No invoices found for order {self.name} (ID {self.id}), sending webhook without payments.")
        return webhook_data

    def _prepare_and_send_webhook(self, webhook_type='order'):
        """
        פונקציה מרכזית שמכינה, בודקת ושולחת את הוובהוק
        
        Args:
            webhook_type (str): סוג הוובהוק - 'order' או 'invoice'
        """
        # ========================================
        # בדיקת סטטוסים בסיסיים
        # ========================================
        
        # בדיקה אם ההזמנה מוגדרת לא לסנכרון
        if self.engini_no_sync:
            # במקום שגיאה, נחזיר הודעה ידידותית
            message = f"הזמנה {self.name} מוגדרת כ'לא לסנכרון'"
            _logger.warning(message)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'לא ניתן לסנכרן',
                    'message': message,
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # בדיקת סטטוס הזמנה
        if self.state not in ['sale', 'done']:
            # במקום שגיאה, נחזיר הודעה ידידותית
            message = f"ניתן לסנכרן רק הזמנות במצב 'sale' או 'done'. הזמנה {self.name} במצב '{self.state}'"
            _logger.warning(message)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'לא ניתן לסנכרן',
                    'message': message,
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # ========================================
        # בדיקות מיוחדות לשליחת הזמנה בלבד
        # ========================================
        
        if webhook_type == 'order':
            # בדיקת VAT (ח.פ) של הלקוח - רק לשליחת הזמנה
            if not self.partner_id.vat:
                message = f"ללקוח {self.partner_id.name} אין מספר ח.פ (VAT). לא ניתן לסנכרן הזמנה לפריורטי ללא ח.פ"
                _logger.warning(message)
                self.message_post(body=message)
                return False
            

        
        # בדיקת מספר ניסיונות
        settings = self.env['engini.settings'].search([('is_primary', '=', True)], limit=1)
        max_retries = settings.max_retry_count if settings else 3
        
        if self.engini_retry_count >= max_retries:
            # במקום שגיאה, נחזיר הודעה ידידותית
            message = f"הזמנה {self.name} הגיעה למספר מקסימלי של ניסיונות ({max_retries})"
            _logger.warning(message)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'לא ניתן לסנכרן',
                    'message': message,
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # ========================================
        # הכנת נתוני הוובהוק
        # ========================================
        
        webhook_data = self._prepare_webhook_data()
        
        # הוספת מטא-דאטה לוובהוק
        webhook_data['webhook_metadata'] = {
            'webhook_type': webhook_type,
            'order_state': self.state,
            'sync_timestamp': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'retry_count': self.engini_retry_count,
            'order_priority': self.engini_priority,
            'total_items': self.engini_total_items,
            'has_discount': self.engini_has_discount,
        }
        
        # ========================================
        # בחירת כתובת URL הנכונה
        # ========================================
        
        if not settings:
            # במקום שגיאה, נחזיר הודעה ידידותית
            message = "לא נמצאו הגדרות פריורטי במערכת"
            _logger.warning(message)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'לא ניתן לסנכרן',
                    'message': message,
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        if webhook_type == 'invoice':
            webhook_url = settings.webhook_invoice_url
            if not webhook_url:
                # במקום שגיאה, נחזיר הודעה ידידותית
                message = "כתובת וובהוק חשבונית לא מוגדרת בהגדרות"
                _logger.warning(message)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'לא ניתן לסנכרן',
                        'message': message,
                        'type': 'warning',
                        'sticky': False,
                    }
                }
        else:  # webhook_type == 'order'
            webhook_url = settings.webhook_open_order_url
            if not webhook_url:
                # במקום שגיאה, נחזיר הודעה ידידותית
                message = "כתובת וובהוק הזמנה לא מוגדרת בהגדרות"
                _logger.warning(message)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'לא ניתן לסנכרן',
                        'message': message,
                        'type': 'warning',
                        'sticky': False,
                    }
                }
        
        # ========================================
        # בדיקות נוספות לפי סוג הוובהוק
        # ========================================
        
        # אין צורך בבדיקות נוספות - שני סוגי הוובהוק מקבלים את אותו JSON
        # ההבדל הוא רק בכתובת הוובהוק
        
        # ========================================
        # עדכון סטטוס לפני שליחה
        # ========================================
        
        self.engini_sync_status = 'pending'
        self.engini_sync_date = fields.Datetime.now()
        
        # ========================================
        # שליחת הנתונים לשרת
        # ========================================
        
        timeout = settings.sync_timeout if settings else 30
        
        # יצירת רשומת היסטוריה
        history_data = {
            'order_id': self.id,
            'webhook_url': webhook_url,
            'data_sent': str(webhook_data),
            'sync_status': 'pending'
        }
        history_record = self.env['engini.sync.history'].create(history_data)
        
        try:
            response = requests.post(webhook_url, json=webhook_data, timeout=timeout)
            response.raise_for_status()
            
            # עדכון היסטוריה בהצלחה
            history_record.write({
                'sync_status': 'synced',
                'response_received': str(response.text),
                'sync_duration': 0  # כאן אפשר לחשב את הזמן האמיתי
            })
            
            _logger.info(f"Order {self.name} sent to webhook successfully (type: {webhook_type})")
            self.message_post(body="ההזמנה עודכנה בפריורטי")
            
        except Exception as e:
            # עדכון היסטוריה בשגיאה
            history_record.write({
                'sync_status': 'failed',
                'error_message': str(e),
                'error_details': f"HTTP request failed: {e}"
            })
            
            _logger.error(f"Failed to send order {self.name}: {e}")
            self.message_post(body=f"שגיאה בשליחת ההזמנה לפריורטי: {e}")
            raise
        
        # החזרת ערך הצלחה
        return True

    def send_to_sales_order_webhook(self):
        """שליחה לוובהוק הזמנה (sync order) - שימוש בפונקציה המרכזית"""
        for order in self:
            try:
                order._prepare_and_send_webhook('order')
            except Exception as e:
                # עדכון סטטוס בשגיאה
                order.engini_sync_status = 'failed'
                order.engini_error_message = str(e)
                order.engini_retry_count += 1
                order.engini_last_retry = fields.Datetime.now()
                raise
    
    def send_to_invoice_webhook(self):
        """שליחת נתוני ההזמנה לוובהוק חשבונית (invoice) - שימוש בפונקציה המרכזית"""
        for order in self:
            try:
                order._prepare_and_send_webhook('invoice')
            except Exception as e:
                # עדכון סטטוס בשגיאה
                order.engini_sync_status = 'failed'
                order.engini_error_message = str(e)
                order.engini_retry_count += 1
                order.engini_last_retry = fields.Datetime.now()
                raise
    
    # ========================================
    # לוגיקות חדשות - סנכרון פריורטי
    # ========================================
    
    # פונקציות חישוב
    @api.depends('order_line.product_uom_qty')
    def _compute_total_items(self):
        """חישוב סה"כ פריטים בהזמנה"""
        for order in self:
            order.engini_total_items = sum(order.order_line.mapped('product_uom_qty'))
    
    @api.depends('order_line.price_unit', 'order_line.discount')
    def _compute_has_discount(self):
        """בדיקה אם יש הנחה בהזמנה"""
        for order in self:
            order.engini_has_discount = any(line.discount > 0 for line in order.order_line)
    
    @api.depends('engini_sync_history_ids')
    def _compute_sync_history_count(self):
        """חישוב מספר הסנכרונים"""
        for order in self:
            order.engini_sync_history_count = len(order.engini_sync_history_ids)
    
    # פעולות סנכרון
    def action_sync_to_engini(self, webhook_type='order'):
        """פעולה לסנכרון ההזמנה לפריורטי - וובהוק הזמנה או חשבונית"""
        for order in self:
            # בדיקה אם ההזמנה מוגדרת כ'לא לסנכרון'
            if order.engini_no_sync:
                message = f"הזמנה {order.name} לא סונכרנה לפריורטי עקב הגדרת 'לא לסנכרון'"
                order.message_post(body=message)
                _logger.info(message)
                continue
            
            try:
                # שימוש בפונקציה המרכזית עם סוג וובהוק
                result = order._prepare_and_send_webhook(webhook_type)
                
                # בדיקה אם הפונקציה החזירה הודעת שגיאה
                if isinstance(result, dict) and result.get('type') == 'ir.actions.client':
                    # הפונקציה החזירה הודעת שגיאה - לא נעדכן סטטוס
                    _logger.warning(f"Order {order.name} {webhook_type} sync blocked: {result.get('params', {}).get('message', 'Unknown error')}")
                    return result
                
                # עדכון סטטוס לאחר הצלחה
                order.engini_sync_status = 'synced'
                order.engini_error_message = False
                order.engini_retry_count = 0
                
                webhook_name = 'Invoice webhook' if webhook_type == 'invoice' else 'Sync Order webhook'
                _logger.info(f"Order {order.name} synced successfully to Engini ({webhook_name})")
                
            except Exception as e:
                # טיפול בשגיאות
                order.engini_sync_status = 'failed'
                order.engini_error_message = str(e)
                order.engini_retry_count += 1
                order.engini_last_retry = fields.Datetime.now()
                
                webhook_name = 'invoice webhook' if webhook_type == 'invoice' else 'order webhook'
                _logger.error(f"Failed to sync order {order.name} to {webhook_name}: {e}")
                raise
    
    def action_sync_invoice_to_engini(self):
        """פעולה לסנכרון החשבונית לפריורטי - וובהוק חשבונית (invoice)"""
        # קריאה לפונקציה המרכזית עם webhook_type='invoice'
        return self.action_sync_to_engini('invoice')
    
    def action_retry_sync(self):
        """פעולה לניסיון חוזר בסנכרון - שימוש בסוג הוובהוק המקורי"""
        for order in self:
            # בדיקה אם ההזמנה מוגדרת כ'לא לסנכרון'
            if order.engini_no_sync:
                message = f"הזמנה {order.name} לא סונכרנה לפריורטי עקב הגדרת 'לא לסנכרון'"
                order.message_post(body=message)
                _logger.info(message)
                continue
            
            if order.engini_sync_status in ['failed', 'not_synced']:
                # בדיקה מה היה סוג הוובהוק האחרון מהיסטוריה
                last_history = order.engini_sync_history_ids.sorted('create_date', reverse=True)[:1]
                
                if last_history and last_history.webhook_url:
                    # זיהוי סוג הוובהוק לפי הכתובת
                    settings = self.env['engini.settings'].search([('is_primary', '=', True)], limit=1)
                    if settings:
                        if last_history.webhook_url == settings.webhook_invoice_url:
                            order.action_sync_invoice_to_engini()
                        else:
                            order.action_sync_to_engini()
                    else:
                        # ברירת מחדל לוובהוק הזמנה
                        order.action_sync_to_engini()
                else:
                    # ברירת מחדל לוובהוק הזמנה
                    order.action_sync_to_engini()
    
    def action_reset_sync_status(self):
        """איפוס סטטוס הסנכרון"""
        for order in self:
            order.engini_sync_status = 'not_synced'
            order.engini_error_message = False
            order.engini_retry_count = 0
            order.engini_sync_date = False
            order.engini_last_retry = False
    
    def action_set_no_sync(self):
        """הגדרת הזמנה כ'לא לסנכרון'"""
        for order in self:
            order.engini_no_sync = True
            order.engini_error_message = False
            order.engini_retry_count = 0
            order.engini_sync_date = False
            order.engini_last_retry = False
            _logger.info(f"Order {order.name} marked as 'no_sync'")
    
    def action_remove_no_sync(self):
        """הסרת הגדרת 'לא לסנכרון'"""
        for order in self:
            if order.engini_no_sync:
                order.engini_no_sync = False
                _logger.info(f"Order {order.name} removed from 'no_sync' status")
    
    def action_view_sync_history(self):
        """צפייה בהיסטוריית הסנכרון של ההזמנה"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'engini.sync.history',
            'view_mode': 'list,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
            'name': f'היסטוריית סנכרון - {self.name}',
        }
    
    def action_show_priority_menu(self):
        """הצגת תפריט פריורטי עם כל האקשנים"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'show_priority_menu': True,
                'default_show_priority_menu': True,
            }
        }
    
    # פעולות המוניות
    @api.model
    def action_bulk_sync_pending_orders(self):
        """סנכרון המוני של הזמנות ממתינות"""
        pending_orders = self.search([
            ('engini_sync_status', 'in', ['not_synced', 'failed']),
            ('state', 'in', ['sale', 'done', 'sent'])
        ])
        
        # סינון הזמנות שמוגדרות לא לסנכרון
        filtered_orders = pending_orders.filtered(lambda o: not o.engini_no_sync)
        
        success_count = 0
        error_count = 0
        
        for order in filtered_orders:
            try:
                order.action_sync_to_engini()
                success_count += 1
            except Exception as e:
                error_count += 1
                _logger.error(f"Bulk sync failed for order {order.name}: {e}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'סנכרון המוני',
                'message': f'הושלם סנכרון המוני: {success_count} הצלחות, {error_count} כשלונות',
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }
    
    @api.model
    def action_check_sync_status(self):
        """בדיקת סטטוס סנכרון של כל ההזמנות"""
        total_orders = self.search_count([('state', 'in', ['sale', 'done'])])
        synced_orders = self.search_count([('engini_sync_status', '=', 'synced')])
        failed_orders = self.search_count([('engini_sync_status', '=', 'failed')])
        pending_orders = self.search_count([('engini_sync_status', '=', 'pending')])
        not_synced_orders = self.search_count([('engini_sync_status', '=', 'not_synced')])
        no_sync_orders = self.search_count([('engini_no_sync', '=', True)])
        
        message = f"""
        סטטוס סנכרון פריורטי:
        • סה"כ הזמנות: {total_orders}
        • מסונכרן: {synced_orders}
        • שגיאה: {failed_orders}
        • ממתין: {pending_orders}
        • לא מסונכרן: {not_synced_orders}
        • לא לסנכרון: {no_sync_orders}
        """
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'סטטוס סנכרון',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
    
    # אירועי מערכת
    @api.model
    def create(self, vals):
        """עדכון אוטומטי של סטטוס סנכרון בעת יצירת הזמנה"""
        record = super().create(vals)
        record.engini_sync_status = 'not_synced'
        return record
    
    def write(self, vals):
        """עדכון סטטוס סנכרון בעת שינוי הזמנה"""
        result = super().write(vals)
        
        # אם יש שינויים משמעותיים, עדכן סטטוס סנכרון
        significant_fields = ['order_line', 'amount_total', 'partner_id', 'date_order']
        if any(field in vals for field in significant_fields):
            for order in self:
                if order.engini_sync_status == 'synced':
                    order.engini_sync_status = 'not_synced'
        
        return result
    
    def action_confirm(self):
        """סנכרון אוטומטי בעת אישור הזמנה"""
        result = super().action_confirm()
        
        # סנכרון אוטומטי אם מוגדר
        settings = self.env['engini.settings'].search([('active', '=', True)], limit=1)
        if settings and settings.auto_sync_on_confirm:
            for order in self:
                if order.engini_sync_status == 'not_synced':
                    try:
                        order.action_sync_to_engini()
                    except Exception as e:
                        _logger.warning(f"Auto sync failed for order {order.name}: {e}")
        
        return result
    
    def action_set_line_no_sync(self):
        """הגדרת שורה כ'לא לסנכרון'"""
        for line in self:
            line.engini_sync_status = 'no_sync'
            _logger.info(f"Line {line.id} marked as 'no_sync'")
    
    def action_remove_line_no_sync(self):
        """הסרת הגדרת 'לא לסנכרון' משורה"""
        for line in self:
            if line.engini_sync_status == 'no_sync':
                line.engini_sync_status = 'not_synced'
                _logger.info(f"Line {line.id} removed from 'no_sync' status")
    
    @api.model
    def action_view_no_sync_orders(self):
        """צפייה בהזמנות שמוגדרות 'לא לסנכרון'"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('engini_no_sync', '=', True)],
            'name': 'הזמנות לא לסנכרון',
            'context': {'search_default_no_sync': 1},
        }


# ========================================
# הערה: הסרנו את ההרחבה לשורות הזמנה כי זה לא נדרש
# הסנכרון נעשה ברמת ההזמנה כולה
# ========================================


# ========================================
# הרחבה להגדרות פריורטי
# ========================================

class EnginiSettings(models.Model):
    _name = 'engini.settings'
    _description = 'הגדרות פריורטי'
    
    # שדה שם
    name = fields.Char(string='שם', required=True, default=lambda self: 'הגדרות פריורטי')
    
    # שדה פעיל
    active = fields.Boolean(string='פעיל', default=True, help='הגדרות אלו פעילות וישמשו לסנכרון')
    
    # שדה הגדרות ראשיות
    is_primary = fields.Boolean(string='הגדרות ראשיות', default=False, help='הגדרות אלו הן הראשיות וישמשו לסנכרון')
    
    # וובהוק ראשון - יצירת חשבונית מס קבלה
    webhook_invoice_url = fields.Char(
        string='Webhook URL - וובהוק חשבונית (invoice)',
        default='https://webhook.site/invoice-webhook',
        help='כתובת וובהוק ליצירת חשבונית מס קבלה'
    )
    
    # וובהוק שני - פתיחת הזמנה ללקוח
    webhook_open_order_url = fields.Char(
        string='Webhook URL - וובהוק הזמנה (sync order)',
        default='https://webhook.site/open-order-webhook',
        help='כתובת וובהוק לפתיחת הזמנה ללקוח (sync order)'
    )
    
    auto_sync_on_confirm = fields.Boolean(
        string='סנכרון אוטומטי בעת אישור',
        default=True,
        help='סנכרון אוטומטי של הזמנות בעת אישורן'
    )
    
    sync_timeout = fields.Integer(
        string='זמן פסקה לסנכרון (שניות)',
        default=30,
        help='זמן מקסימלי לסנכרון לפני פסקה'
    )
    
    max_retry_count = fields.Integer(
        string='מספר ניסיונות מקסימלי',
        default=3,
        help='מספר ניסיונות מקסימלי לסנכרון'
    )
    
    def action_test_connection(self):
        """בדיקת חיבור לשרת פריורטי"""
        try:
            # שליחת בקשת בדיקה לוובהוק של החשבוניות
            test_data = {
                'test': True,
                'message': 'בדיקת חיבור ממודול פריורטי - וובהוק חשבוניות',
                'timestamp': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # שימוש בפונקציה המרכזית לשליחה
            self._prepare_and_send_webhook(webhook_type='invoice')
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'בדיקת חיבור',
                    'message': 'החיבור לשרת פריורטי הצליח!',
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'שגיאה בחיבור',
                    'message': f'שגיאה בחיבור לשרת פריורטי: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def action_test_status(self):
        """בדיקת סטטוס שרת פריורטי"""
        try:
            # בדיקת סטטוס בסיסי
            settings = self.env['engini.settings'].search([('is_primary', '=', True)], limit=1)
            if not settings:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'שגיאה',
                        'message': 'לא נמצאו הגדרות ראשיות לבדיקת סטטוס',
                        'type': 'warning',
                        'sticky': False,
                    }
                }
            
            # בדיקת URL-ים
            invoice_url = settings.webhook_invoice_url or 'לא הוגדר'
            order_url = settings.webhook_open_order_url or 'לא הוגדר'
            
            # בדיקת הגדרות נוספות
            auto_sync = 'פעיל' if settings.auto_sync_on_confirm else 'לא פעיל'
            timeout = f"{settings.sync_timeout} שניות"
            retries = f"{settings.max_retry_count} ניסיונות"
            
            status_message = f"""
            סטטוס שרת פריורטי:
            • וובהוק חשבוניות: {invoice_url}
            • וובהוק הזמנות: {order_url}
            • סנכרון אוטומטי: {auto_sync}
            • זמן פסקה: {timeout}
            • מספר ניסיונות: {retries}
            """
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'סטטוס שרת פריורטי',
                    'message': status_message,
                    'type': 'info',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'שגיאה בבדיקת סטטוס',
                    'message': f'שגיאה בבדיקת סטטוס שרת פריורטי: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def action_activate_settings(self):
        """הפעלת הגדרות אלו כראשיות"""
        for record in self:
            # ביטול הגדרות ראשיות אחרות
            other_primary = self.env['engini.settings'].search([
                ('id', '!=', record.id),
                ('is_primary', '=', True)
            ])
            if other_primary:
                other_primary.with_context(skip_is_primary_logic=True).write({'is_primary': False})
            
            # הפעלת ההגדרות הנוכחיות כראשיות
            record.with_context(skip_is_primary_logic=True).write({
                'is_primary': True,
                'active': True
            })
            
            message = f"הגדרות '{record.name}' הופעלו כראשיות. הגדרות אחרות בוטלו."
            _logger.info(message)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'הגדרות הופעלו',
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_deactivate_settings(self):
        """ביטול הגדרות אלו כראשיות"""
        for record in self:
            record.with_context(skip_is_primary_logic=True).write({'is_primary': False})
            
            # אם אין הגדרות ראשיות אחרות, הפעל הגדרות אחרות
            other_settings = self.env['engini.settings'].search([
                ('id', '!=', record.id),
                ('active', '=', True)
            ], limit=1)
            
            if other_settings:
                other_settings.with_context(skip_is_primary_logic=True).write({'is_primary': True})
                message = f"הגדרות '{record.name}' בוטלו כראשיות. הגדרות '{other_settings.name}' הופעלו אוטומטית."
            else:
                message = f"הגדרות '{record.name}' בוטלו כראשיות."
            
            _logger.info(message)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'הגדרות בוטלו',
                    'message': message,
                    'type': 'warning',
                    'sticky': False,
                }
            }

    @api.model
    def create(self, vals):
        """יצירת הגדרות חדשות עם בדיקה שרק אחד ראשי"""
        # אם זה הראשי, בטל אחרים
        if vals.get('is_primary'):
            self.env['engini.settings'].with_context(skip_is_primary_logic=True).search([
                ('is_primary', '=', True)
            ]).with_context(skip_is_primary_logic=True).write({'is_primary': False})
        
        return super().create(vals)

    def write(self, vals):
        """עדכון הגדרות עם בדיקה שרק אחד ראשי"""
        # אם לא מדלגים על הלוגיקה של is_primary
        if not self.env.context.get('skip_is_primary_logic'):
            # אם זה הופך לראשי, בטל אחרים
            if vals.get('is_primary'):
                other_primary = self.env['engini.settings'].search([
                    ('id', 'not in', self.ids),
                    ('is_primary', '=', True)
                ])
                if other_primary:
                    other_primary.with_context(skip_is_primary_logic=True).write({'is_primary': False})
        
        return super().write(vals)


# ========================================
# הרחבה להיסטוריית סנכרון פריורטי
# ========================================

class EnginiSyncHistory(models.Model):
    _name = 'engini.sync.history'
    _description = 'היסטוריית סנכרון פריורטי'
    _order = 'create_date desc'
    
    # שדות בסיסיים
    name = fields.Char(string='שם', required=True, default=lambda self: 'סנכרון חדש')
    order_id = fields.Many2one('sale.order', string='הזמנה', required=True, ondelete='cascade')
    order_name = fields.Char(string='מספר הזמנה', related='order_id.name', store=True)
    
    # שדות סטטוס
    sync_status = fields.Selection([
        ('pending', 'ממתין לסנכרון'),
        ('synced', 'מסונכרן'),
        ('failed', 'שגיאה בסנכרון'),
        ('cancelled', 'בוטל')
    ], string='סטטוס', default='pending', tracking=True)
    
    # שדות תאריך
    sync_date = fields.Datetime(string='תאריך סנכרון', default=fields.Datetime.now)
    sync_duration = fields.Float(string='משך סנכרון (שניות)', readonly=True)
    
    # שדות שגיאה
    error_message = fields.Text(string='הודעת שגיאה')
    error_details = fields.Text(string='פרטי שגיאה')
    
    # שדות נתונים
    data_sent = fields.Text(string='נתונים שנשלחו')
    response_received = fields.Text(string='תגובה שהתקבלה')
    
    # שדות נוספים
    retry_count = fields.Integer(string='מספר ניסיונות', default=0)
    webhook_url = fields.Char(string='כתובת Webhook')
    
    # שדות חישוב
    is_successful = fields.Boolean(string='הצליח', compute='_compute_is_successful', store=True)
    sync_age_hours = fields.Float(string='גיל הסנכרון (שעות)', compute='_compute_sync_age')
    
    @api.depends('sync_status')
    def _compute_is_successful(self):
        """חישוב האם הסנכרון הצליח"""
        for record in self:
            record.is_successful = record.sync_status == 'synced'
    
    @api.depends('sync_date')
    def _compute_sync_age(self):
        """חישוב גיל הסנכרון בשעות"""
        for record in self:
            if record.sync_date:
                delta = datetime.now() - record.sync_date
                record.sync_age_hours = delta.total_seconds() / 3600
            else:
                record.sync_age_hours = 0
    
    def action_retry_sync(self):
        """ניסיון חוזר בסנכרון"""
        for record in self:
            if record.sync_status in ['failed', 'cancelled']:
                try:
                    record.sync_status = 'pending'
                    record.sync_date = fields.Datetime.now()
                    record.retry_count += 1
                    
                    # שליחת ההזמנה
                    record.order_id.send_to_sales_order_webhook()
                    
                    record.sync_status = 'synced'
                    record.error_message = False
                    record.error_details = False
                    
                    _logger.info(f"Retry sync successful for order {record.order_id.name}")
                    
                except Exception as e:
                    record.sync_status = 'failed'
                    record.error_message = str(e)
                    record.error_details = f"Retry attempt {record.retry_count} failed: {e}"
                    _logger.error(f"Retry sync failed for order {record.order_id.name}: {e}")
    
    def action_cancel_sync(self):
        """ביטול הסנכרון"""
        for record in self:
            if record.sync_status == 'pending':
                record.sync_status = 'cancelled'
                record.error_message = 'בוטל על ידי המשתמש'
    
    def action_view_order(self):
        """צפייה בהזמנה"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def create(self, vals):
        """יצירת רשומה חדשה"""
        if not vals.get('name'):
            vals['name'] = f"סנכרון {fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return super().create(vals)
    
    def write(self, vals):
        """עדכון רשומה"""
        if 'sync_status' in vals and vals['sync_status'] == 'synced':
            vals['sync_duration'] = 0  # כאן אפשר לחשב את הזמן האמיתי
        return super().write(vals)
    
    @api.model
    def action_cleanup_old_history(self):
        """ניקוי היסטוריית סנכרון ישנה (מעל 30 ימים)"""
        from datetime import timedelta
        
        cutoff_date = fields.Datetime.now() - timedelta(days=30)
        old_records = self.search([
            ('create_date', '<', cutoff_date),
            ('sync_status', 'in', ['synced', 'failed', 'cancelled'])
        ])
        
        deleted_count = len(old_records)
        old_records.unlink()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'ניקוי היסטוריה',
                'message': f'נמחקו {deleted_count} רשומות ישנות מהיסטוריית הסנכרון',
                'type': 'success',
                'sticky': False,
            }
        }


# ========================================
# הרחבה ל-bulk runner פריורטי
# ========================================

class EnginiWebhookBulkRunner(models.Model):
    _name = 'engini.webhook.bulk.runner'
    _description = 'Bulk Runner פריורטי'
    
    name = fields.Char(string='שם', required=True)
    description = fields.Text(string='תיאור')
    
    # שדות הגדרות
    batch_size = fields.Integer(string='גודל קבוצה', default=10)
    timeout = fields.Integer(string='זמן פסקה (שניות)', default=30)
    
    # שדות סטטוס
    state = fields.Selection([
        ('draft', 'טיוטה'),
        ('running', 'רץ'),
        ('done', 'הושלם'),
        ('failed', 'שגיאה')
    ], string='סטטוס', default='draft', tracking=True)
    
    # שדות תוצאות
    total_records = fields.Integer(string='סה"כ רשומות', readonly=True)
    processed_records = fields.Integer(string='רשומות שעובדו', readonly=True)
    success_count = fields.Integer(string='הצלחות', readonly=True)
    error_count = fields.Integer(string='כשלונות', readonly=True)
    
    # שדות תאריך
    start_date = fields.Datetime(string='תאריך התחלה', readonly=True)
    end_date = fields.Datetime(string='תאריך סיום', readonly=True)
    
    # שדות שגיאה
    error_message = fields.Text(string='הודעת שגיאה', readonly=True)
    
    def action_start_bulk_run(self):
        """התחלת ריצה המונית"""
        for runner in self:
            try:
                # בדיקת הגדרות וובהוק פעילות
                settings = self.env['engini.settings'].search([('is_primary', '=', True)], limit=1)
                if not settings or not settings.webhook_invoice_url:
                    # במקום שגיאה, נחזיר הודעה ידידותית
                    message = "לא הוגדרה כתובת וובהוק ליצירת חשבונית בהגדרות"
                    _logger.warning(message)
                    runner.state = 'failed'
                    runner.error_message = message
                    return
                
                runner.state = 'running'
                runner.start_date = fields.Datetime.now()
                runner.processed_records = 0
                runner.success_count = 0
                runner.error_count = 0
                runner.error_message = False
                
                # כאן תהיה הלוגיקה של הריצה ההמונית
                _logger.info(f"Started bulk run: {runner.name} with webhook: {settings.webhook_invoice_url}")
                
            except Exception as e:
                runner.state = 'failed'
                runner.error_message = str(e)
                _logger.error(f"Bulk run failed: {e}")
    
    def action_stop_bulk_run(self):
        """עצירת ריצה המונית"""
        for runner in self:
            if runner.state == 'running':
                runner.state = 'failed'
                runner.error_message = 'נעצר על ידי המשתמש'
                _logger.info(f"Bulk run stopped: {runner.name}")
    
    def action_reset_bulk_run(self):
        """איפוס ריצה המונית"""
        for runner in self:
            runner.state = 'draft'
            runner.processed_records = 0
            runner.success_count = 0
            runner.error_count = 0
            runner.error_message = False
            runner.start_date = False
            runner.end_date = False


# ========================================
# הערה: השדות פריורטי מוגדרים במודל PriorityCustomer נפרד
# אין צורך להרחיב את ResPartner עם אותם שדות
# ========================================


# ========================================
# סיכום - כל המודלים במקום אחד
# ========================================
"""
הקובץ הזה מכיל את כל ההרחבות למודול פריורטי:

1. SaleOrder - הרחבה להזמנות מכירה
   - שדות סנכרון פריורטי
   - לוגיקות סנכרון
   - פעולות המוניות

2. SaleOrderLine - הרחבה לשורות הזמנה
   - שדות סנכרון לשורות
   - לוגיקות חישוב

3. EnginiSettings - הגדרות פריורטי
   - הגדרות Webhook
   - הגדרות סנכרון

4. EnginiSyncHistory - היסטוריית סנכרון
   - מעקב אחר סנכרונים
   - ניהול שגיאות

5. EnginiWebhookBulkRunner - ריצה המונית
   - ריצה המונית של סנכרונים
   - ניהול תהליכים

6. ResPartner - הרחבה לכרטיס לקוח
   - שדות פריורטי בסיסיים
   - מפתחות זיהוי

כל המודלים מסודרים במקום אחד עם הפרדה ברורה בין שדות ללוגיקות.
"""

from odoo import models, api
import requests
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_webhook_data(self):
        webhook_data = {
            'order_id': self.id,
            'name': self.name,
            'date_order': self.date_order.strftime('%Y-%m-%d %H:%M:%S'),
            'partner': {
                'name': self.partner_id.name,
                'phone': self.partner_id.phone,
                'mobile': self.partner_id.mobile,
                'email': self.partner_id.email,
                'vat': self.partner_id.vat,
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
            line_data = {
                'product': line.product_id.name,
                'default_code': line.product_id.default_code,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
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

    def _send_webhook_data(self, webhook_data):
        webhook_url = self.env['engini.settings'].search([], limit=1).webhook_url
        try:
            response = requests.post(webhook_url, json=webhook_data, timeout=10)
            response.raise_for_status()
            _logger.info("Order %s sent to webhook." % self.name)
            self.message_post(body="ההזמנה עודכנה בפריורטי")
        except Exception as e:
            _logger.error("Failed to send order %s: %s" % (self.name, str(e)))
            self.message_post(body=f"שגיאה בשליחת ההזמנה לפריורטי: {e}")
            raise

    def send_to_webhook(self):
        for order in self:
            webhook_data = order._prepare_webhook_data()
            order._send_webhook_data(webhook_data)

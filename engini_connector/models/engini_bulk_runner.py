from odoo import models, fields
import time
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class EnginiWebhookBulkRunner(models.TransientModel):
    _name = 'engini.webhook.bulk.runner'
    _description = 'Engini Webhook Bulk Runner'

    order_names_raw = fields.Text(string="Order Names")
    delay_seconds = fields.Integer(string="Delay (seconds)", default=4, min=4)
    use_custom_date = fields.Boolean(string="Use Custom Date", default=False)
    custom_date = fields.Date(string="Custom Order Date")

    def _parse_order_names(self):
        if not self.order_names_raw:
            return []
        return list(filter(None, [x.strip() for x in self.order_names_raw.replace(',', '\n').splitlines()]))

    def run_button(self):
        if self.delay_seconds < 4:
            raise ValidationError("השהייה בין שליחות חייבת להיות לפחות 4 שניות.")
        order_names = self._parse_order_names()
        self.run_from_names(order_names)

    def run_from_names(self, order_names):
        _logger.info("🚀 Starting bulk webhook sending")

        missing_orders = []
        sent_orders = []
        failed_orders = []

        for order_name in order_names:
            order = self.env['sale.order'].search([('name', '=', order_name)], limit=1)

            if not order:
                missing_orders.append(order_name)
                continue

            _logger.info(f"📤 Sending order {order.name} (ID {order.id}) to webhook...")
            _logger.info(f"📦 Webhook data for order {order.name}: {order._prepare_webhook_data()}")

            try:
                # Create a copy of the order's webhook data
                webhook_data = order._prepare_webhook_data()
                
                # Override the date if checkbox is checked and date is set
                if self.use_custom_date and self.custom_date:
                    webhook_data['date_order'] = self.custom_date.isoformat()
                
                # Send the modified webhook data
                order._send_webhook_data(webhook_data)
                
                sent_orders.append(order.name)
                _logger.info(f"✅ Order {order.name} sent successfully.")
            except Exception as e:
                failed_orders.append(order.name)
                _logger.error(f"🚨 Error sending order {order.name}: {str(e)}")
                continue

            if order_name != order_names[-1]:  # Don't wait after the last order
                _logger.info(f"⏳ Waiting {self.delay_seconds} seconds...")
                time.sleep(self.delay_seconds)

        summary_lines = []

        summary_lines.append("🏁 Finished sending orders.")

        if sent_orders:
            summary_lines.append(f"✅ {len(sent_orders)} orders sent successfully:")
            summary_lines.append(", ".join(sent_orders))

        if failed_orders:
            summary_lines.append(f"🚨 {len(failed_orders)} orders failed during sending:")
            summary_lines.append(", ".join(failed_orders))

        if missing_orders:
            summary_lines.append(f"❌ {len(missing_orders)} order names not found in system:")
            summary_lines.append(", ".join(missing_orders))

        _logger.info("\n".join(summary_lines))
        self.log_to_odoo("\n".join(summary_lines), level='info')

    def log_to_odoo(self, message, level='info'):
        self.env['ir.logging'].create({
            'name': 'engini.bulk.runner',
            'type': 'server',
            'dbname': self.env.cr.dbname,
            'level': level,
            'message': message,
            'path': 'engini_bulk_runner',
            'line': 0,
            'func': 'run_from_names',
        }) 
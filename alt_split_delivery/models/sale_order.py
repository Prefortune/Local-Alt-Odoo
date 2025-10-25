from operator import le
from signal import raise_signal
from tarfile import data_filter
from odoo import models, fields, api, _ ,SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import secrets
import logging
_logger = logging.getLogger(__name__)

class PriceListReport(models.AbstractModel):
    _name = 'report.alt_split_delivery.report_split_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    
    def generate_xlsx_report(self, workbook, data, trainsnet_records):
        _logger.info("Generating report with data %s", data)

        bold = workbook.add_format({'bold': True})
        sheet = workbook.add_worksheet("Split Deliveries")

        # Define headers and corresponding column widths
        headers = ['Order Number', 'Email', 'Name', 'Surname', 'Phone', 'City', 'Street', 'Zip Code']
        column_widths = [15, 30, 20, 20, 15, 20, 30, 10]

        # Set column widths for readability
        for col_num, width in enumerate(column_widths):
            sheet.set_column(col_num, col_num, width)

        # Write header row
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, bold)

        row = 1
        for record in trainsnet_records:

            orders = self.env['sale.order'].sudo().search([
                ('date_order', '>=', record.date_start),
                ('date_order', '<=', record.date_end),
                ('state', '!=', 'draft'),
                ('alt_split_delivery_count', '>', 1),
            ])
            _logger.info("---- orders getting---- %s",orders)

            filtered_orders = orders.filtered(lambda x: len(x.picking_ids) >= x.alt_split_delivery_count)

            _logger.info("filterd_orders->-------------- %s", [rec.name for rec in filtered_orders])
            if not filtered_orders:
                raise ValidationError(f"There Is No Any Split Delivery Order Between {record.date_start} To {record.date_end}")
            
            for order in filtered_orders:
                for picking in order.picking_ids.filtered(lambda x : x.state != 'done'):
                    address = picking.partner_id
                    sheet.write(row, 0, order.name or '')
                    sheet.write(row, 1, address.email or '')
                    sheet.write(row, 2, address.name or '')
                    surname = address.name.split(' ')[-1] if address.name else ''
                    sheet.write(row, 3, surname)
                    sheet.write(row, 4, address.phone or '')
                    sheet.write(row, 5, address.city or '')
                    sheet.write(row, 6, address.street or '')
                    sheet.write(row, 7, address.zip or '')
                    row += 1



class Trainsnet(models.TransientModel):
    _name = 'split.trainsnet.report'
    _description = 'Split Trainsnet Delivery Report'

    date_start = fields.Date(string="Start Order Date")
    date_end = fields.Date(string="End Order Date")

    # @api.constrains('date_start', 'date_end')
    # def _check_dates(self):
    #     for record in self:
    #         if not record.date_start or not record.date_end:
    #             raise ValidationError("The Start Date And The End Date Is Required.")
    #         if record.date_start and record.date_end and record.date_start > record.date_end:
    #             raise ValidationError("The start date cannot be after the end date.")

    def close_button(self):
        return {'type': 'ir.actions.act_window_close'}

    def generate_report(self):

        if not self.date_start or not self.date_end:
                raise ValidationError("The Start Date And The End Date Is Required.")
        if self.date_start and self.date_end and self.date_start > self.date_end:
                raise ValidationError("The start date cannot be after the end date.")
        
        _logger.info("Generating report for dates %s to %s", self.date_start, self.date_end)
        return self.env.ref('alt_split_delivery.report_split_xlsx').report_action(self)



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    alt_split_delivery_count = fields.Integer(string='כמות משלוחים', default=1)
    alt_split_delivery_note = fields.Char(string="הערה למשלוח", readonly=True)
    alt_split_delivery_total_price = fields.Monetary(string='עלות משלוחים כוללת', default=0.0, currency_field='currency_id')
    alt_split_delivery_url = fields.Char(string='Delivey Url', compute='_compute_alt_split_delivery_url')
    customer_delivery_date = fields.Date(string="Customer Expacted Delivery Date")
    greeting_card = fields.Text(string="Greeting Card")
    delivery_note = fields.Text(string="Delivery Note")
    split_access_token = fields.Char('Split Access Token', readonly=True)
    split_delivery_status = fields.Selection([
        ('normal_order','Normal Order'),
        ('not_file', 'Not Filed'),
        ('filed', 'Filed'),
        ('delivered', 'Delivered Split Delivery')
    ], string="Split Delivery Status", default='not_file',compute="_compute_split_delivery_status",store=True)

    # @api.depends('picking_ids')
    @api.depends('picking_ids.state', 'alt_split_delivery_count')
    def _compute_split_delivery_status(self):
        # _logger.info("-------- _compute_split_delivery_status---------- %s",self.name)
        for order in self:
            # _logger.info("_compute_split_delivery_status is called for order %s", order.id)
            if order.alt_split_delivery_count > 1:
                if not order.picking_ids:
                    order.split_delivery_status = 'not_file'
                elif all(p.state == 'done' for p in order.picking_ids):
                    order.split_delivery_status = 'delivered'
                elif len(order.picking_ids) >= order.alt_split_delivery_count:
                    order.split_delivery_status = 'filed'
                else:
                    order.split_delivery_status = 'not_file'
            else:
                order.split_delivery_status = 'normal_order'


    def copy(self, default=None):
        default = default or {}
        # Always create a new token for copied order
        default['split_access_token'] = secrets.token_urlsafe(16)
        return super().copy(default)

    def _compute_alt_split_delivery_url(self):
        for order in self:
            if not order.split_access_token:
               order.split_access_token = secrets.token_urlsafe(16)
            order.alt_split_delivery_url = f"/my/orders/{order.id}/{order.split_access_token}/split_delivery"

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
                self.message_post(body=f' שימו לב! בהזמנה זו יש משלוחים מפוצלים – יש לטפל בהתאם.')
                _logger.info("carrier_id for order %s , %s",carrier_id.name,self.name)
                delivery_product = carrier_id.product_id
                for line in self.order_line.filtered(lambda x : x.product_id == delivery_product and x.product_type == 'service'):
                    line.name = f'{line.name} - ({self.alt_split_delivery_count})'
                # template = self.env.ref("alt_split_delivery.pf_mail_template_sale_multi_shipping", raise_if_not_found=False)
                mail_template = self.env.ref('alt_split_delivery.pf_mail_template_sale_multi_shipping')
                email_values = {
                    'email_to': self.partner_id.email
                }
                _logger.info("######## mail_template is ######### %s , %s",mail_template , self.id)
                mail_template.with_user(SUPERUSER_ID).send_mail(self.id, force_send=True , email_values=email_values)
                _logger.info("######## Template email_to: %s", mail_template.email_to)
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
    
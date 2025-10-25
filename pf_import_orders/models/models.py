from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
import base64
import xlrd
import csv
from io import StringIO
import time

class ProductProduct(models.Model):
    _inherit = 'product.template'

    is_script_product = fields.Boolean(string="Is Script Product",default=False)

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    is_script_order = fields.Boolean(string="Is Script Sales Order")
    csv_ref = fields.Char(string="Csv Ref")

class CronList(models.Model):
    _name = 'cron.list'

    name = fields.Char(string='Name',default='Order Cron')
    status = fields.Selection([('pending','Pending'),('running','Running'),('complete','Complete')],default='pending')
    last_cursor = fields.Integer(string="last cursor",default=2) 

class ImportOrders(models.Model):
    _name = 'import.orders'

    file_data = fields.Binary(string="Upload File")


    def click_me(self):
        for res in self:
            cron_list = self.env['cron.list'].search([],limit=1)
            if not cron_list:
                self.env['cron.list'].create({
                    'name' : 'Order Cron',
                    'status' : 'pending',
                    'last_cursor' : 1
                })
                return {'type': 'ir.actions.client', 'tag': 'reload'}
            return {'type': 'ir.actions.client', 'tag': 'reload'}

            # self.env.ref('pf_import_orders.ir_cron_pf_sync_orders').method_direct_trigger()

        
    def action_import_csv(self):
        
        _logger.info("------------------- import order cron is start from cron job-------------------")

        start_time = time.time()
        _logger.info("------- start time of my cron ----- %s",start_time)

        cron_list = self.env['cron.list'].search([('status','in',['pending','running'])],limit=1)
        if not cron_list:
            _logger.info("No pending/running cron found, exiting...")
            return
        
        last_cursor = cron_list.last_cursor
        _logger.info(f"Resuming from cursor position: {last_cursor}")

        cron_obj = self.env['import.orders'].search([],limit=1)
        for res in cron_obj:
            
            cron_list.write({
            'status' : 'running'
        })
            
            if not res.file_data:
                _logger.info("---------- file is not found ----------")
                return

            search_tax = self.env['account.tax'].search([
                ('amount_type', '=', 'percent'),
                ('type_tax_use', '=', 'sale'),
                ('active', '=', True),
                ('amount','=',5.0000)
            ],limit=1)
            if search_tax:
                tax_id = search_tax.id
            else:
                tax_id = self.env['account.tax'].create({
                    'name': '5% Tax',
                    'amount_type': 'percent',
                    'type_tax_use': 'sale',
                    'amount': 5.0000,
                    'active': True
                    }).id

            """Reads the uploaded CSV and creates sales orders, lines, and payments"""

            try:
                csv_data = base64.b64decode(res.file_data or b"")
                data_file = StringIO(csv_data.decode("utf-8"))
                reader = csv.DictReader(data_file)
                # sale_orders = {}
                count = 0

            except Exception as e:
                _logger.error(f"Error decoding file data: {e}")
                return
            
            for _ in range(last_cursor - 1):  
                next(reader, None)

            current_cursor = last_cursor
            for row in reader:

                if time.time() - start_time > 62:

                        cron_list.write({
                            'last_cursor' : current_cursor 
                        })

                        _logger.info(f"Stopping cron at row {current_cursor}, will resume next cycle.")
                        return True
            
                current_cursor += 1

                _logger.info("Processing row number: %s",  row)
                _logger.info("count time: %s",  time.time() - start_time)

                date = row.get("Date")
                receipt_number = row.get("Receipt Number")
                line_type = row.get("Line Type")
                customer_code = row.get("Customer Code")
                customer_name = row.get("Customer Name")
                note = row.get("Note")

                # Handling Quantity
                if row.get("Quantity", 0) == 0 or row.get("Quantity", "").strip() == "":
                    quantity = 0.0
                else:
                    quantity = float(row.get("Quantity", 0))

                # Handling Subtotal
                if row.get("Subtotal", 0) == 0 or row.get("Subtotal", "").strip() == "":
                    subtotal = 0.0
                else:
                    subtotal = float(row.get("Subtotal", 0))

                # Handling Discount
                if row.get("Discount", 0) == 0 or row.get("Discount", "").strip() == "":
                    discount = 0.0
                else:
                    discount = float(row.get("Discount", 0))

                # Handling Sales Tax
                if row.get("Sales Tax", 0) == 0 or row.get("Sales Tax", "").strip() == "":
                    sales_tax = 0.0
                else:
                    sales_tax = float(row.get("Sales Tax", 0))

                # Handling Total
                if row.get("Total", 0) == 0 or row.get("Total", "").strip() == "":
                    total = 0.0
                else:
                    total = float(row.get("Total", 0))

                paid = row.get("Paid")
                sku = row.get("Sku")
                user = row.get("User")
                status = row.get("Status")


                partner = self.env["res.partner"].search([("name", "=", customer_name)], limit=1)
                if not partner:
                    partner = self.env["res.partner"].create({
                        "name": customer_name,
                        "ref": customer_code,
                    })
            
                
                if line_type == "Sale":

                    sale_orders = self.env['sale.order'].search([('csv_ref','=',receipt_number)],limit=1)

                    _logger.info("data is getting %s , %s",date , type(date))
                    if not sale_orders:
 
                        sale_order = self.env["sale.order"].create({
                            "partner_id": partner.id,
                            "note": note, 
                            "date_order" : date,
                            "is_script_order" : True,
                            'csv_ref' : receipt_number,
                            'tag_ids' : [(4,1)],
                        })
                        # self.env.cr.commit()
                        _logger.info("sales order is create %s",sale_order.name)

                
                elif line_type == "Sale Line" and receipt_number:

                    sale_orders = self.env['sale.order'].search([('csv_ref','=',receipt_number)],limit=1)

                    product_template = self.env["product.template"].search([("default_code", "=", sku)], limit=1)
                    if not product_template:
                        product_template = self.env["product.template"].create({
                            "name": row.get("Details"),
                            "default_code": sku,
                            "is_script_product" : True,
                            "detailed_type" : "consu",
                            "invoice_policy" : "order"
                        })

                    product = product_template.product_variant_id

                    
                    self.env["sale.order.line"].create({
                        "order_id": sale_orders.id,
                        "product_id": product.id,
                        "product_uom_qty": abs(quantity),
                        "price_unit": subtotal / abs(quantity) if quantity !=0 else subtotal,
                        "tax_id": [(6, 0, [tax_id])] if sales_tax else [(6, 0, [])]
                    })

                    # sales_object = self.env["sale.order"].browse(sale_orders[receipt_number])
                    
                    if sale_orders.state == "draft":
                        sale_orders.action_confirm()
                        sale_orders.write({
                            "date_order" : date
                        })
                        
                        # picking = sales_object.picking_ids.filtered(lambda p: p.state == "assigned")
                        # if picking:
                        #     picking.button_validate()


                elif line_type == "Payment" and receipt_number:

                    sale_orders = self.env['sale.order'].search([('csv_ref','=',receipt_number)],limit=1)
                    # sales_object = self.env["sale.order"].browse(sale_orders[receipt_number])

                    # if sale_orders and sale_orders.order_line and sale_orders.invoice_count <= 0:
                    if sale_orders and sale_orders.order_line:

                        if any(line.qty_to_invoice > 0 for line in sale_orders.order_line) and sale_orders.amount_total > 0:
                            invoice_id = sale_orders._create_invoices()
                            invoice_id.write({
                                'invoice_date': sale_orders.date_order,
                                'invoice_date_due' : sale_orders.date_order
                            })
                            if invoice_id.amount_total > 0:
                                invoice_id.action_post()
                                create_payment_register = self.env['account.payment.register'].with_context({'active_model': 'account.move', 'active_ids': [invoice_id.id]}).create({
                                    'payment_date' : sale_orders.date_order
                                }).action_create_payments()
                            else:
                                _logger.warning(f"Invoice for Sale Order {sale_orders.name} has a negative amount. Creating a credit note instead.")
                        else:
                            _logger.warning(f"Sale order {sale_orders.name} has no invoiceable lines. Or Sales Order Total Is Negetive")

            products = self.env['product.template'].search([(
                'is_script_product', '=', True
            )])
            for product in products:
                product.write({
                    'active' : False
                })

        cron_list.write({
            'status' : 'complete',
            'last_cursor' : current_cursor
        })

        action= {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Info',
                            'message': "Sales Order Are Created From Csv Please Check",
                            'sticky': True, 
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                }
        
        return action


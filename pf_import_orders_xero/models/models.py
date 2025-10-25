from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
import base64
import xlrd
import csv
from io import StringIO
import time
import datetime

class ProductProduct(models.Model):
    _inherit = 'product.template'

    is_script_product = fields.Boolean(string="Is Script Product",default=False)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_xero_order = fields.Boolean(string="Is Xero Order")
    xero_ref = fields.Char(string="Xero Ref")

class CronList(models.Model):
    _name = 'cron.list.xero'

    name = fields.Char(string='Name',default='Order Cron')
    status = fields.Selection([('pending','Pending'),('running','Running'),('complete','Complete')],default='pending')
    last_cursor = fields.Integer(string="last cursor",default=2) 


class ImportOrders(models.Model):
    _name = 'import.orders.xero'

    file_data = fields.Binary(string="Upload File")


    def click_me(self):
        for res in self:
            cron_list = self.env['cron.list.xero'].search([],limit=1)
            if not cron_list:
                self.env['cron.list.xero'].create({
                    'name' : 'Order Cron Xero',
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

        cron_list = self.env['cron.list.xero'].search([('status','in',['pending','running'])],limit=1)
        if not cron_list:
            _logger.info("No pending/running cron found, exiting...")
            return
        
        last_cursor = cron_list.last_cursor
        _logger.info(f"Resuming from cursor position: {last_cursor}")

        cron_obj = self.env['import.orders.xero'].search([],limit=1)
        for res in cron_obj:
            
            cron_list.write({
            'status' : 'running'
        })
            
            if not res.file_data:
                _logger.info("---------- file is not found ----------")
                return

            search_tax = self.env['account.tax'].search([
                ('amount_type', '=', 'percent'),
                ('type_tax_use', '=', 'purchase'),
                ('active', '=', True),
                ('amount','=',5.0000)
            ],limit=1)
            if search_tax:
                tax_id = search_tax.id
            else:
                tax_id = self.env['account.tax'].create({
                    'name': 'Purchase Tax @ 5%',
                    'amount_type': 'percent',
                    'type_tax_use': 'purchase',
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

                _logger.info("--- Processing row number --- %s",row)
                if time.time() - start_time > 62:

                        cron_list.write({
                            'last_cursor' : current_cursor 
                        })

                        _logger.info(f"Stopping cron at row {current_cursor}, will resume next cycle.")
                        return True
            
                current_cursor += 1

                invoice_date_raw = row.get("InvoiceDate", "").strip()
                due_date_raw = row.get("DueDate", "").strip()

                invoice_date = None
                date_planned = None

                # Handle invoice date
                try:
                    if invoice_date_raw:
                        invoice_date = datetime.datetime.strptime(invoice_date_raw, '%d/%m/%Y').date()
                except ValueError:
                    _logger.warning("Invalid InvoiceDate format: %s. Skipping or falling back.", invoice_date_raw)

                # Handle due date
                try:
                    if due_date_raw:
                        date_planned = datetime.datetime.strptime(due_date_raw, '%d/%m/%Y').date()
                    elif invoice_date:
                        date_planned = invoice_date  # If due date is empty, use invoice date
                except ValueError:
                    _logger.warning("Invalid DueDate format: %s. Falling back to InvoiceDate if possible.", due_date_raw)
                    if invoice_date:
                        date_planned = invoice_date

                # Final fallback if everything is broken
                if not invoice_date:
                    invoice_date = datetime.date.today()
                if not date_planned:
                    date_planned = invoice_date  # Final fallback to invoice_date if due date is invalid or missing

                invoice_number = row.get("InvoiceNumber")
                reference = row.get("Reference")
                # line_type = row.get("Line Type")
                # customer_code = row.get("Customer Code")
                customer_name = row.get("ContactName")
                customer_email = row.get("EmailAddress")
                street = row.get("POAddressLine1")
                street2 = row.get("POAddressLine2")
                country_id = row.get("POCountry")
                state_id = row.get("PORegion")
                city = row.get("POCity")
                country_code = row.get("POPostalCode")
                currency = row.get("Currency")

                if country_id.strip():

                    if country_id == 'UAE':
                        country_id = 'United Arab Emirates'
                    country_id = self.env['res.country'].search([('name','=',country_id)])

                if state_id.strip():
                    state_id = self.env['res.country.state'].search([('name','=',state_id)])

                # Handling Quantity
                if row.get("Quantity", 0) == 0 or row.get("Quantity", "").strip() == "":
                    quantity = 0.0
                else:
                    quantity = float(row.get("Quantity", 0))

                # Handling Subtotal
                if row.get("UnitAmount", 0) == 0 or row.get("UnitAmount", "").strip() == "":
                    subtotal = 0.0
                else:
                    subtotal = float(row.get("UnitAmount", 0))

                # Handling Discount
                if row.get("Discount", 0) == 0 or row.get("Discount", "").strip() == "":
                    discount = 0.0
                else:
                    discount = float(row.get("Discount", 0))

                # Handling Sales Tax
                if row.get("TaxAmount", 0) == 0 or row.get("TaxAmount", "").strip() == "":
                    purchase_tax = 0.0
                else:
                    purchase_tax = float(row.get("TaxAmount", 0))

                # Handling Total
                if row.get("Total", 0) == 0 or row.get("Total", "").strip() == "":
                    total = 0.0
                else:
                    total = float(row.get("Total", 0))

                type = row.get("Type")
                product_name = row.get("Description")
                payment_status = row.get("Status")


                partner = self.env["res.partner"].search([("name", "=", customer_name)], limit=1)
                if not partner:
                    partner = self.env["res.partner"].create({
                        "name": customer_name if customer_name else 'Csv Customer',
                        "email" : customer_email if customer_email else '',
                        "street" : street if street else '',
                        "street2" : street2 if street2 else '',
                        "city" : city,
                        "country_id" : country_id.id if country_id else None,
                        "state_id" : state_id.id if state_id else None,
                        "zip" : country_code,
                        # "ref": customer_code,
                    })
            
                if not invoice_number:
                    invoice_number = reference.strip()
                    _logger.info("unique invoice number is not found --- replace with reference %s",invoice_number)

                if invoice_number and type:
                    purchase_order = self.env['purchase.order'].search([('xero_ref','=',invoice_number)],limit=1)
                    if not purchase_order:
                        
                        if currency.strip():
                            currency_id = self.env['res.currency'].search([('name', '=', currency), ('active', '=', True)], limit=1)
                            
                            if not currency_id:
                                # Try to find inactive currency with the same name
                                currency_inactive = self.env['res.currency'].search([('name', '=', currency)], limit=1)
                                if currency_inactive:
                                    currency_inactive.active = True  # Activate it
                                    currency_id = currency_inactive
                                else:
                                    # Fallback to AED
                                    currency_id = self.env['res.currency'].search([('name', '=', 'AED'), ('active', '=', True)], limit=1)

                            currency = currency_id
                            
                        # if currency.strip():
                        #     currency_id = self.env['res.currency'].search([('name','=',currency),('active','=',True)])
                        #     if currency_id:
                        #         currency = currency_id
                        #     else:
                        #         currency = self.env['res.currency'].search([('name','=','AED'),('active','=',True)])
                                
                        purchase_order = self.env["purchase.order"].create({
                            "partner_id": partner.id,
                            "date_order" : invoice_date,
                            "is_xero_order" : True,
                            "currency_id" : currency.id,
                            "xero_ref" : invoice_number,
                            # 'tag_ids' : [(4,1)],
                        })
                        # self.env.cr.commit()
                        _logger.info("Purchase order is create %s",purchase_order.name)

                
                    product_template = self.env["product.template"].search([("name", "=", product_name)], limit=1)
                    if product_template and product_template.invoice_policy == 'delivery':
                        product_template.write({'invoice_policy' : 'order'})
                    if not product_template:
                        product_template = self.env["product.template"].create({
                            "name": product_name,
                            "is_script_product" : True,
                            "detailed_type" : "consu",
                            "invoice_policy" : "order"
                        })

                    product = product_template.product_variant_id

                    if abs(quantity) > 0:
                        self.env["purchase.order.line"].create({
                            "order_id": purchase_order.id,
                            "product_id": product.id,
                            "product_qty": abs(quantity) ,
                            "price_unit": subtotal,
                            "taxes_id": [(6, 0, [tax_id])] if purchase_tax else [(6, 0, [])]
                        })
                        if purchase_order.state == "draft":
                            purchase_order.button_confirm()
                            purchase_order.write({
                                "date_approve" : invoice_date,
                                "date_planned" : date_planned
                            })

                        picking_ids = purchase_order.picking_ids
                        if picking_ids:
                            for picking in purchase_order.picking_ids.filtered(lambda p: p.state not in ['done', 'cancel']):
                                picking.button_validate()
                        
                        if purchase_order and purchase_order.order_line:
                            # if any(line.product_qty > 0 for line in purchase_order.order_line) and purchase_order.amount_total > 0:
                                # bill_id = purchase_order._create_invoices()
                                bill = purchase_order.action_create_invoice()
                                bill_ids = purchase_order.invoice_ids
                                for bill_id in bill_ids:
                                    # _logger.info("---- bill name ------ %s",bill_id.name)
                                    # _logger.info("bill id -------------- %s",bill_id)
                                    # _logger.info("bill_id name --- %s",bill_id.name)
                                    bill_id.write({
                                        'invoice_date': invoice_date,
                                        'date' : invoice_date,
                                        'invoice_date_due' : date_planned,
                                        'name': '/',  # Always reset to regenerate sequence
                                    })
                                    if bill_id.state != 'posted' and bill_id.amount_total > 0:
                                            bill_id.action_post()
                                            if payment_status == 'Paid':
                                                create_payment_register = self.env['account.payment.register'].with_context({'active_model': 'account.move', 'active_ids': [bill_id.id]}).create({
                                                    'payment_date' : invoice_date
                                                }).action_create_payments()
                                        # else:
                                            # _logger.warning(f"Bill for Purchase Order {bill_id.name} has a negative amount. Creating a credit note instead.")
                            # else:
                            #     _logger.warning(f"Purchase order {purchase_order.name} has no invoiceable lines. Or Purchase Order Total Is Negetive")
                    # else:
                    #     pass


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
                            'message': "Purchase Order Are Created From Csv Please Check",
                            'sticky': True, 
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                }
        
        return action


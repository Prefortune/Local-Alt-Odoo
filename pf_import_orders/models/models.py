from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
import base64
import xlrd
import csv
from io import StringIO
import time
import re
class ResPartner(models.Model):
    _inherit = 'res.partner'

    old_mobile = fields.Char("Old Mobile")


class CronList(models.Model):
    _name = 'cron.list'

    name = fields.Char(string='Name',default='Order Cron')
    status = fields.Selection([('pending','Pending'),('running','Running'),('complete','Complete')],default='pending')
    last_cursor = fields.Integer(string="last cursor",default=2) 

class ImportOrders(models.Model):
    _name = 'pfimport.orders'

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

        cron_obj = self.env['pfimport.orders'].search([],limit=1)
        for res in cron_obj:
            
            cron_list.write({
            'status' : 'running'
        })
            
            if not res.file_data:
                _logger.info("---------- file is not found ----------")
                return

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

                ID = row.get("ID")
                Mobile = row.get("Mobile")
                Phone = row.get("Phone")
                
                try:
                    partner_id = int(ID)
                except (TypeError, ValueError):
                    continue

                partner = self.env["res.partner"].browse(partner_id)

                if not partner or not partner.exists():
                    continue

               
                partner.write({'old_mobile': partner.mobile}) 

                partner_mobile = Mobile or Phone or partner.mobile or partner.phone

                if not partner_mobile:
                    continue

                # partner.write({'old_mobile': partner_mobile})

                partner_mobile = partner_mobile.strip()
                partner_mobile = re.sub(r'[^0-9+]', '', partner_mobile)

                if not partner_mobile:
                    continue

                country_code = self.env['res.country'].search([('code','=','IL')]).phone_code
                if not country_code:
                    continue

                if partner_mobile.startswith(f'+{country_code}'):
                        pass  # keep as is
                
                elif partner_mobile.startswith(str(country_code)):
                    partner_mobile = f'+{partner_mobile}'

                else:
                    partner_mobile = f'+{country_code}{partner_mobile}'

                partner.write({'mobile': partner_mobile})

                _logger.info("Updated partner %s mobile: %s", partner.id, partner_mobile)

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


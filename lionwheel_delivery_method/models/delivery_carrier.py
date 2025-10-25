from odoo import models, fields, api

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    # LionWheel API Configuration
    lionwheel_api_key = fields.Char(string='LionWheel API Key', help='Your LionWheel API key for authentication')
    lionwheel_org_key = fields.Char(string='LionWheel Organization Key', help='Your LionWheel organization key for company-level operations')
    lionwheel_company_id = fields.Char(string='Company ID', help='Company ID to associate the task with')
    lionwheel_api_url = fields.Char(string='API URL', default='https://members.lionwheel.com/api/v1/tasks/create', help='LionWheel API endpoint URL')
    
    # LionWheel Source Address Configuration
    lionwheel_source_city = fields.Char(string='Source City', default='ירושלים', help='Source city for shipments')
    lionwheel_source_street = fields.Char(string='Source Street', default='רבי טרפון', help='Source street for shipments')
    lionwheel_source_number = fields.Char(string='Source Number', default='4', help='Source street number for shipments')
    lionwheel_source_zip_code = fields.Char(string='Source Zip Code', help='Source zip code for shipments')
    lionwheel_source_recipient_name = fields.Char(string='Source Recipient Name', default='Leaf of Life', help='Source recipient name for shipments')
    lionwheel_source_phone = fields.Char(string='Source Phone', default='972587040400', help='Source phone number for shipments')
    lionwheel_source_email = fields.Char(string='Source Email', default='office@leafoflife.co.il', help='Source email for shipments')
    
    # LionWheel Delivery Settings
    lionwheel_default_packages_quantity = fields.Integer(string='Default Packages Quantity', default=1, help='Default number of packages per shipment')
    lionwheel_default_urgency = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Urgent'),
        ('2', 'Very Urgent')
    ], string='Default Urgency', default='0', help='Default urgency level for shipments')
    lionwheel_is_roundtrip = fields.Boolean(string='Is Roundtrip', default=False, help='Whether shipments are roundtrip by default')
    lionwheel_is_self_pickup = fields.Boolean(string='Is Self Pickup', default=False, help='Whether shipments are self pickup by default')
    
    # LionWheel Time Settings
    lionwheel_default_earliest = fields.Char(string='Default Earliest Time', help='Default earliest delivery time (e.g., 09:00)')
    lionwheel_default_latest = fields.Char(string='Default Latest Time', help='Default latest delivery time (e.g., 18:00)')
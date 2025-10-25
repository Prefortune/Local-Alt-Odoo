from odoo import models, fields

class Website(models.Model):
    _inherit = 'website'

    enable_guest_checkout = fields.Boolean(string="Enable Guest Checkout", default=False)
    enable_company_vat_visible = fields.Boolean(string="Enable Company VAT Visiblity", default=False)
    enable_set_delivery_date = fields.Boolean(string="Enable Set Delivery Date Visiblity",default=False)


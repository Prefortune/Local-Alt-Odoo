from odoo import models, fields, api

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    customer_code = fields.Char(string='Customer Code')
    cargo_delivery_type = fields.Selection([('box', 'BOX'), ('express', 'EXPRESS'),('cargo', 'CARGO')], string='Delivery Type')

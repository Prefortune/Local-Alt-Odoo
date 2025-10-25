from odoo import models, fields

class StickyButtonConfig(models.Model):
    _name = 'sticky.button.config'
    _description = 'Sticky Button Configuration'
    _rec_name = 'button_text'

    button_text = fields.Char(string="Button Text", default="להצעת מחיר")
    button_url = fields.Char(string="Button URL", default="#Offer") 
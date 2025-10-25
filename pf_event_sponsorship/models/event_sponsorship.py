from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class eventSponsorship(models.Model):
    _name = 'event.sponsorship'
    _description = 'Event Sponsorship'

    event_id = fields.Many2one('event.event', string="Event", required=True)
    sponsorship_type = fields.Selection([
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('bronze', 'Bronze'),
    ], string="Sponsorship Type", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    sponsorship_amount = fields.Monetary(string="Sponsorship Amount", required=True,currency_field='currency_id') 
    sponsorship_description = fields.Html(string="Sponsorship Description")
    

    # get the value of the sponsorship_type field
    def get_sponsorship_type_display(self):
        return dict(self._fields['sponsorship_type'].selection).get(self.sponsorship_type)
    

   
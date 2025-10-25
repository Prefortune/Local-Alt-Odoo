from odoo import models, fields,api
import logging
_logger = logging.getLogger(__name__)

class SponsorshipPaymentSession(models.Model):
    _name = 'sponsorship.payment.session'
    _description = 'Sponsorship Payment Session'

    event_id = fields.Many2one('event.event', string="Event", required=True)
    sponsorship_id = fields.Many2one('event.sponsorship', required=True)
    session_id = fields.Char(required=True)
    name= fields.Char(string="CardHolder Name", required=True)
    customer_email = fields.Char()
    phone = fields.Char(string="Phone Number")
    sponsorship_type = fields.Char()
    amount_total = fields.Float()
    payment_status = fields.Char()
    currency = fields.Char()
   

    amount_with_currency = fields.Char(string="Amount", compute="_compute_amount_with_currency")

    @api.depends('amount_total', 'currency')
    def _compute_amount_with_currency(self):
        for record in self:
            if record.currency:
                symbol = self.env['res.currency'].search([('name', '=', record.currency)], limit=1).symbol or record.currency
                record.amount_with_currency = f"{symbol} {record.amount_total:.2f}"
            else:
                record.amount_with_currency = f"{record.amount_total:.2f}"



    def create_payment_session(self):
        _logger.info("Creating payment session...................................")
    
    
    # pf_event_sponsorship.access_stripe_webhook,access_stripe_webhook,pf_event_sponsorship.model_stripe_webhook,base.group_user,1,1,1,1

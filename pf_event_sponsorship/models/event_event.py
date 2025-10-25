from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class EventEvent(models.Model):
    _inherit = 'event.event'

    active_sponsorship = fields.Boolean(string="Active Sponsorship", default=False)

    event_sponsorship_ids = fields.One2many(
        'event.sponsorship',
        'event_id',
        string="Event Sponsorship",
    )

    event_sponsorship_payment_ids = fields.One2many(
        'sponsorship.payment.session',
        'event_id',
        string="Event Sponsorship Payment Sessions",
    )


    
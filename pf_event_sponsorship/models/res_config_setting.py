from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class ResConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    # stripe_publishable_key = fields.Char(string="Stripe Publishable Key", config_parameter='pf_event_sponsorship.stripe_publishable_key')
    stripe_secret_key = fields.Char(string="Stripe Secret Key", config_parameter='pf_event_sponsorship.stripe_secret_key')
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class PaymentProviderCardcom(models.Model):
    _inherit = 'payment.provider'

    # code = fields.Selection(selection_add=[('cardcom_pos', 'CardCom Pos')],ondelete={'cardcom_pos': 'set default'})
    # cardcom_pos_cardcom_terminal_number = fields.Char('Terminal Number', required_if_provider='cardcom')
    # cardcom_pos_cardcom_api_name = fields.Char('API Name', required_if_provider='cardcom')
    # cardcom_pos_cardcom_api_password = fields.Char('API Password', required_if_provider='cardcom')
    # cardcom_pos_success_redirect_url = fields.Char("Success Redirect Url")
    # cardcom_pos_failed_redirect_url = fields.Char("Failed Redirect URL")
    # cardcom_pos_webhook_url = fields.Char("Webhook URL")

    code = fields.Selection(selection_add=[('cardcom_pos', 'CardCom Pos')],ondelete={'cardcom_pos': 'set default'})
    cardcom_pos_cardcom_terminal_number = fields.Char('Terminal Number')
    cardcom_pos_cardcom_api_name = fields.Char('API Name')
    cardcom_pos_cardcom_api_password = fields.Char('API Password')
    cardcom_pos_webhook_url = fields.Char("Webhook URL")
    

import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class PaymentProviderCardcom(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('payplus', 'Payplus')],ondelete={'payplus': 'set default'})

    test_url = fields.Char(
        'Test URL',
        help="The URL for the test environment of PayPlus.",
    )
    production_url = fields.Char(
        'Production URL',
        help="The URL for the production environment of PayPlus.",
    )

    test_page_uid = fields.Char(
        'Test Page UID',
        help="The UID for the test page, used to identify the test environment.",
    )
    production_page_uid = fields.Char(
        'Production Page UID',  
        help="The UID for the production page, used to identify the live environment.",
    )
    
    test_api_key = fields.Char(
        'Test API Key',
        help="The API key for the test environment.",
    )
    production_api_key = fields.Char(
        'Production API Key',
        help="The API key for the production environment.",
    )

    test_secret_key = fields.Char(
        'Test Secret Key',
        help="The secret key for the test environment.",
    )
    production_secret_key = fields.Char(
        'Production Secret Key',
        help="The secret key for the production environment.",
    )

    success_redirect_url = fields.Char("Success Redirect Url")
    failed_redirect_url = fields.Char("Failed Redirect URL")
    webhook_url = fields.Char("Webhook URL")

    payplus_charge_method = fields.Selection(
        [('1','Charge'),('2','Approval')],
        string="Payplus Charge Method",
        default='1'
    )
    send_email_approval = fields.Boolean(
        'Payplus Send Email Approval',
        default=True,
    )
    send_email_failure = fields.Boolean(
        'Payplus Send Email Failure',
        default=False,
    )

    @api.constrains('code', 'state')
    def check_credentials(self):
        for res in self:
            _logger.info("Checking credentials for payment provider: %s %s", res.code, res.state)
            """Check if the credentials are set for the payment provider."""
            if res.code == 'payplus':
                if res.state == 'test':
                    if not res.test_page_uid or not res.test_api_key or not res.test_secret_key:
                        raise ValidationError("Test credentials are not set for Payplus.")
                elif res.state == 'enabled':
                    if not res.production_page_uid or not res.production_api_key or not res.production_secret_key:
                        raise ValidationError("Production credentials are not set for Payplus.")


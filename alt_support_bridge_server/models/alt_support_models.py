import secrets
import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AltSupportToken(models.Model):
    _name = 'alt.support.token'
    _description = 'API Token for Alt Support'

    name = fields.Char(
        string='Name',
        required=True,
        help="A descriptive name for this token. This helps identify the token's purpose or the client it's associated with."
    )
    token = fields.Char(
        string='Client Token',
        required=True,
        default=lambda self: secrets.token_urlsafe(32),
        help="The API token used by the client to authenticate with the server. "
             "This is automatically generated when creating a new token."
    )
    server_token = fields.Char(
        string='Server Token',
        required=True,
        default=lambda self: secrets.token_urlsafe(32),
        help="The token used by the server to authenticate with the client. "
             "This should be copied to the client's configuration."
    )
    url = fields.Char(
        string='Client URL',
        required=True,
        help="The URL of the client's Odoo instance where messages will be sent."
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, this token will be disabled and cannot be used for authentication. "
             "Use this to temporarily disable access without deleting the token."
    )
    create_date = fields.Datetime(
        string='Created on',
        readonly=True,
        help="The date and time when this token was created."
    )

    @api.model
    def create(self, vals):
        if not vals.get('token'):
            vals['token'] = secrets.token_urlsafe(32)
        return super(AltSupportToken, self).create(vals)

    def _update_config_parameter(self):
        """Update the system parameter with all active tokens."""
        active_tokens = self.search([('active', '=', True)])
        token_config = {
            token.name: {
                'token': token.token,
                'server_token': token.server_token,
                'url': token.url
            }
            for token in active_tokens
        }
        self.env['ir.config_parameter'].sudo().set_param(
            'alt_support.valid_tokens',
            str(token_config)
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AltSupportToken, self).create(vals_list)
        self._update_config_parameter()
        return records

    def write(self, vals):
        result = super(AltSupportToken, self).write(vals)
        self._update_config_parameter()
        return result

    def unlink(self):
        result = super(AltSupportToken, self).unlink()
        self._update_config_parameter()
        return result 
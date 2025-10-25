import secrets
from odoo import models, fields, api

class AltSupportConfig(models.Model):
    _name = 'alt.support.config'
    _description = 'Alt Support Configuration'

    server_url = fields.Char(string="Support Server URL")
    api_token = fields.Char(string="API Token")
    server_token = fields.Char(string="Server Token", help="Token used by server to authenticate with this client")

    @api.model
    def create(self, vals):
        # Don't auto-generate server_token - let user paste it from server
        record = super(AltSupportConfig, self).create(vals)
        record._update_config_parameter()
        return record

    def write(self, vals):
        result = super(AltSupportConfig, self).write(vals)
        self._update_config_parameter()
        return result

    def _update_config_parameter(self):
        """Update the system parameter with the server token."""
        config = self.search([], limit=1)
        if config and config.server_token:
            self.env['ir.config_parameter'].sudo().set_param(
                'alt_support.server_token',
                config.server_token
            ) 
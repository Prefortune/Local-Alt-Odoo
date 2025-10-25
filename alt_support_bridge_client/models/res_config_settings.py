from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alt_support_server_url = fields.Char(
        string="Support Server URL",
        config_parameter='alt_support.server_url'
    )
    alt_support_api_token = fields.Char(
        string="API Token",
        config_parameter='alt_support.api_token'
    ) 
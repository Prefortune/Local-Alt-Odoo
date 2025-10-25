from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wa_template_id = fields.Many2one('wa.template', config_parameter='whatsapp_login.otp_whatsapp_template')
    provider_id = fields.Many2one('provider', config_parameter='whatsapp_login.provider')
    wa_reset_password_enabled = fields.Boolean('Reset Password Using WhatsApp', config_parameter='whatsapp_login.wa_reset_password')
    wa_reset_password_template_id = fields.Many2one('wa.template', config_parameter='whatsapp_login.reset_password_whatsapp_template')
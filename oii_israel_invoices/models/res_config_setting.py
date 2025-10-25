import base64
from cryptography.fernet import Fernet
from hashlib import md5
from odoo import _, fields, models, api


class ResConfigSettings(models.TransientModel):
    _name = 'res.config.settings'
    _inherit = ['res.config.settings', 'oii.invoices.base']

    enable_taxes_integration = fields.Boolean(
        related='company_id.enable_taxes_integration',
        readonly=False
    )
    rt_taxes_host = fields.Char(
        related='company_id.rt_taxes_host',
        readonly=False
    )
    rt_taxes_access_token = fields.Char(
        related='company_id.rt_taxes_access_token',
        readonly=False
    )
    rt_taxes_refresh_token = fields.Char(
        related='company_id.rt_taxes_refresh_token',
        readonly=False
    )
    rt_taxes_minimum_untaxed_amount = fields.Integer(
        related='company_id.rt_taxes_minimum_untaxed_amount',
        readonly=False
    )
    rt_client_id = fields.Char(
        related='company_id.rt_client_id',
        readonly=False
    )
    rt_client_secret = fields.Char(
        related='company_id.rt_client_secret',
        readonly=False
    )
    rt_taxes_client_id = fields.Char("Taxes Client_id", config_parameter='rt_taxes_client_id', default='')
    rt_taxes_client_secret = fields.Char("Taxes Client_key", config_parameter='rt_taxes_client_secret', default='')

    def refresh_token(self):
        company_id = self.env.company
        key = md5(company_id.vat.encode()).digest()
        fernet_key_base64 = base64.urlsafe_b64encode(key.ljust(32, b'\0'))
        fernet = Fernet(fernet_key_base64)
        self.env['ir.config_parameter'].set_param('rt_taxes_client_id', fernet.encrypt(self.rt_client_id.encode()))
        self.env['ir.config_parameter'].set_param('rt_taxes_client_secret', fernet.encrypt(self.rt_client_secret.encode()))
        encrypted_client_id = self.env['ir.config_parameter'].sudo().get_param('rt_taxes_client_id')
        encrypted_client_secret = self.env['ir.config_parameter'].sudo().get_param('rt_taxes_client_secret')
        decrypted_client_id = fernet.decrypt(encrypted_client_id.encode()).decode()
        decrypted_secret = fernet.decrypt(encrypted_client_secret.encode()).decode()

        # TEST a request : get refresh token
        endpoint = 'longtimetoken/oauth2/token'
        values = {
            "client_id": decrypted_client_id,
            "scope": 'scope',
            "refresh_token": company_id.rt_taxes_refresh_token,
            "grant_type": 'refresh_token',
            "client_secret": decrypted_secret,
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        status, response = self._do_request(endpoint, params=values, headers=headers, method='POST', type='setting')
        action = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
        if status == 200 and response.get('access_token'):
            company_id.rt_taxes_access_token = response.get('access_token')
            company_id.rt_taxes_refresh_token = response.get('refresh_token')
            action['params'].update({
                'type': 'success',
                'title': _('Success'),
                'message': _("Generated token successfully"),
                'sticky': False,
            })
        else:
            msg = _("Token generation failed, check log.")
            action['params'].update({
                'type': 'danger',
                'title': _('Failure'),
                'message': msg,
                'sticky': True,
            })
            activity_type = self.env.ref('mail.mail_activity_data_todo')
            if activity_type:
                activity_data = {
                    'activity_type_id': activity_type.id,
                    'res_id': self.env.ref('base.user_admin').partner_id.id,
                    'res_model_id': self.env.ref('base.model_res_partner').id,
                    'date_deadline': fields.Date.today(),
                    'user_id': self.env.ref('base.user_admin').id,
                    'note': msg,
                }
                self.env['mail.activity'].create(activity_data)

        return action

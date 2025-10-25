from odoo import models, fields, api, _
import functools
import re
from odoo.exceptions import UserError

compress = functools.partial(re.sub, r'\s', '')

class WhatsAppAuthTotp(models.Model):
    _name = 'whatsapp.auth.totp'

    verify_otp = fields.Char('Verify OTP', size=6)
    user_id = fields.Many2one('res.users', required=True, readonly=True)

    def activate_whatsapp_auth_totp(self):
        try:
            c = int(compress(self.verify_otp))
        except ValueError:
            raise UserError(_("The verification code should only contain numbers"))
        if c == int(self.user_id.partner_id.otp_text):
            self.user_id.totp_whatsapp_enabled = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _("2-Factor authentication with Whatsapp is now enabled."),
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        raise UserError(_('Verification failed, please double-check the 6-digit code'))
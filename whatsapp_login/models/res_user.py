from odoo import api, fields, models, _, SUPERUSER_ID
import functools
import logging
import contextlib
import re
from odoo import _, api, fields, models
from odoo.addons.base.models.res_users import check_identity
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request
from datetime import datetime, timedelta
import pytz

_logger = logging.getLogger(__name__)

compress = functools.partial(re.sub, r'\s', '')

def now(**kwargs):
    return datetime.now() + timedelta(**kwargs)

class ResUsers(models.Model):
    _inherit = 'res.users'

    totp_whatsapp_enabled = fields.Boolean(string="Two-factor authentication using Whatsapp")
    
    def _mfa_type(self):
        r = super()._mfa_type()
        if r is not None:
            return r
        if self.totp_whatsapp_enabled:
            return 'totp_whatsapp'

    def _mfa_url(self):
        r = super()._mfa_url()
        if r is not None:
            return r
        if self._mfa_type() == 'totp_whatsapp':
            return '/web/login/whatsapp-totp'

    @check_identity
    def action_whatsapp_totp_disable(self):
        logins = ', '.join(map(repr, self.mapped('login')))
        if not (self == self.env.user or self.env.user._is_admin() or self.env.su):
            _logger.info("2FA disable: REJECT for %s (%s) by uid #%s", self, logins, self.env.user.id)
            return False

        self.revoke_all_devices()
        self.totp_whatsapp_enabled = False
        _logger.info("2FA for whatsapp disable: SUCCESS for %s (%s) by uid #%s", self, logins, self.env.user.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'warning',
                'message': _("Two-factor authentication disabled for the following user(s): %s",
                             ', '.join(self.mapped('name'))),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


    @check_identity
    def action_totp_whatsapp_enable_wizard(self):
        if self.env.user != self:
            raise UserError(_("Two-factor authentication using whatsapp can only be enabled for yourself"))

        if self.totp_whatsapp_enabled:
            raise UserError(_("Two-factor authentication using whatsapp already enabled"))

        provider = self.env['ir.config_parameter'].sudo().get_param('whatsapp_login.provider')
        provider_id = self.env['provider'].sudo().browse(int(provider))
        wa_template_id = self.env['ir.config_parameter'].sudo().get_param('whatsapp_login.otp_whatsapp_template')
        whatsapp_template = self.env['wa.template'].sudo().browse(int(wa_template_id))

        if provider_id and whatsapp_template:
            composer = request.env['wa.compose.message'].with_user(provider_id.user_id.id).with_context(
                default_model=self.partner_id._name,
                default_res_id=self.partner_id.id,
                default_template_id=whatsapp_template.id,
                default_partner_id=self.partner_id.id,
            ).create({})
            composer.send_whatsapp_message()
        w = self.env['whatsapp.auth.totp'].create({
            'user_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_model': 'whatsapp.auth.totp',
            'name': _("Two-Factor Authentication with WhatsApp Activation"),
            'res_id': w.id,
            'views': [(False, 'form')],
            'context': self.env.context,
        }

    def whatsapp_reset_password(self, mobile):
        users = self.search([]).filtered(lambda x: x.partner_id.mobile == mobile.strip('+'))
        if not users:
            raise Exception(_('No account found for this mobile number'))
        if len(users) > 1:
            raise Exception(_('Multiple accounts found for this mobile number'))
        return users.action_whatsapp_reset_password()

    def action_whatsapp_reset_password(self):
        try:
            if self.filtered(lambda user: not user.active):
                raise UserError(_("You cannot perform this action on an archived user."))
            create_mode = bool(self.env.context.get('create_user'))

            expiration = False if create_mode else now(days=+1)

            self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)


            for user in self:
                provider = self.env['ir.config_parameter'].sudo().get_param('whatsapp_login.provider')
                provider_id = self.env['provider'].sudo().browse(int(provider))
                wa_template_id = self.env['ir.config_parameter'].sudo().get_param(
                    'whatsapp_login.reset_password_whatsapp_template')
                whatsapp_template = self.env['wa.template'].sudo().browse(int(wa_template_id))

                if not user.partner_id.mobile:
                    raise UserError(_("Cannot send whatsapp message: user linked partner %s has no mobile number.", user.partner_id.name))
                with contextlib.closing(self.env.cr.savepoint()):
                     if provider_id and whatsapp_template:
                         composer = request.env['wa.compose.message'].with_user(
                             provider_id.user_id.id).with_context(
                             default_model=self.partner_id._name,
                             default_res_id=self.partner_id.id,
                             default_template_id=whatsapp_template.id,
                             default_partner_id=self.partner_id.id,
                         ).create({})
                         composer.send_whatsapp_message()
                     else:
                         raise UserError(_("Reset password whatsapp template not configured"))
                _logger.info("Password reset whatsapp message sent for user <%s> to <%s>", user.login, user.partner_id.mobile)
        except Exception as e:
            raise UserError(e)


    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        if not password:
            raise AccessDenied()
        ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
        
        if request.params.get('otp'):
            try:
                with cls.pool.cursor() as cr:
                    self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                    with self._assert_can_auth():
                        user = self.search(self._get_login_domain(login), order=self._get_login_order(), limit=1)
                        if not user:
                            raise AccessDenied()
                        user = user.with_user(user)
                        self.env.cr.execute(
                            "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                            [user.id]
                        )
                        hashed = self.env.cr.fetchone()[0]
                        if not password == hashed:
                            user._check_credentials(password, user_agent_env)
    
                        tz = request.httprequest.cookies.get('tz') if request else None
                        if tz in pytz.all_timezones and (not user.tz or not user.login_date):
                            # first login or missing tz -> set tz to browser tz
                            user.tz = tz
                        user._update_last_login()
    
            except AccessDenied:
                _logger.info("Login failed for db:%s login:%s from %s", db, login, ip)
                raise
    
            _logger.info("Login successful for db:%s login:%s from %s", db, login, ip)
    
            return user.id
        else:
            return super()._login(db, login, password, user_agent_env)

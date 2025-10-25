from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.home import Home, ensure_db
from datetime import datetime
import re
import functools
from odoo.exceptions import UserError
import werkzeug
import logging
import json
import requests

compress = functools.partial(re.sub, r'\s', '')
_logger = logging.getLogger(__name__)

class CustomLoginController(Home):

    @http.route(website=True)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        if request.httprequest.method == 'GET':
            response = super(CustomLoginController, self).web_login(redirect, **kw)
        else:
            if request.params.get('login'):
                kw.update({'login':request.params['login'].strip()})
            if request.params.get('password'):
                kw.update({'password': request.params['password'].strip()})
            response = super(CustomLoginController, self).web_login(redirect, **kw)
        response.qcontext.update(self.get_wa_auth_signup_config())
        return response

    def get_config_provider_template(self):
        provider = request.env['ir.config_parameter'].sudo().get_param('whatsapp_login.provider')
        provider_id = request.env['provider'].sudo().browse(int(provider))
        wa_template_id = request.env['ir.config_parameter'].sudo().get_param(
            'whatsapp_login.otp_whatsapp_template')
        whatsapp_template = request.env['wa.template'].sudo().browse(int(wa_template_id))
        return provider_id, whatsapp_template

    def get_wa_auth_signup_config(self):
        """retrieve the module config (which features are enabled) for the login page"""

        get_param = request.env['ir.config_parameter'].sudo().get_param
        return {
            'wa_reset_password_enabled': get_param('whatsapp_login.wa_reset_password') == 'True',
        }

    def _send_otp_message_to_public_user(self, wa_template, provider_id, mobile):
        if wa_template.category == 'authentication':
                params = []
                otp = wa_template.generate_secure_otp(wa_template.otp_length)
                request.session['otp'] = otp
                for component in wa_template.components_ids:
                    if component.type == 'body' and component.text:
                        params.append({'type': 'body',
                                              'parameters': [{'type': 'text',
                                           'text': otp}]})

                    if component.type == 'buttons' and component.wa_button_ids:
                        wa_buttons = component.wa_button_ids.filtered(lambda button: button.button_type == 'url' and button.url_type == 'dynamic')
                        if wa_buttons:
                            for button in wa_buttons:
                                dynamic_index = {button: i for i, button in
                                                 enumerate(wa_buttons)}
                                params.append({
                                    'type': 'button',
                                    'sub_type': 'URL',
                                    'index': dynamic_index.get(button),
                                    'parameters': [{'type': 'text',
                                                    'text': otp}]})
                url = "https://graph.facebook.com/v20.0/" + provider_id.graph_api_instance_id + "/messages"
                payload = json.dumps({
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": mobile,
                    "type": "template",
                    "template": {
                        "name": wa_template.name,
                        "language": {
                            "code": wa_template.language
                        },
                        "components": params
                    }
                })
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + provider_id.graph_api_token
                }
                requests.post(url, headers=headers, data=payload)

    @http.route(
        '/web/login/whatsapp-totp',
        type='http', auth='public', methods=['GET', 'POST'], sitemap=False,
        website=True, multilang=False
    )
    def web_whatsapp_totp(self, redirect=None, **kwargs):
        if request.session.uid:
            return request.redirect(self._login_redirect(request.session.uid, redirect=redirect))

        if not request.session.pre_uid:
            return request.redirect('/web/login')
        mobile, error, otp_invalid, otp_sent = False, False, False, False
        user = request.env['res.users'].sudo().browse(request.session.pre_uid)
        if user and request.httprequest.method == 'GET':
            mobile = '*' * 10 + user.partner_id.mobile[10:]
            provider_id, whatsapp_template = self.get_config_provider_template()
            if provider_id and whatsapp_template:
                composer = request.env['wa.compose.message'].with_user(provider_id.user_id.id).with_context(
                    default_model=user.partner_id._name,
                    default_res_id=user.partner_id.id,
                    default_template_id=whatsapp_template.id,
                    default_partner_id=user.partner_id.id,
                ).create({})
                composer.send_whatsapp_message()
            otp_sent = True

        elif user and request.httprequest.method == 'POST' and kwargs.get('otp'):
            try:
                otp = int(compress(kwargs.get('otp')))
            except ValueError:
                raise UserError(_("The verification code should only contain numbers"))
            except ValueError:
                error = _("Invalid authentication code format.")
            else:
                if user and (datetime.now() - user.partner_id.otp_time).total_seconds() > 600:
                    return request.render('whatsapp_login.wa_auth_totp_otp_verification_template', {'otp_expired': True})
                elif otp == int(user.partner_id.otp_text):
                    request.session.finalize(request.env)
                    request.update_env(user=request.session.uid)
                    request.update_context(**request.session.context)
                    response = request.redirect(self._login_redirect(request.session.uid, redirect=redirect))
                    # Crapy workaround for unupdatable Odoo Mobile App iOS (Thanks Apple :@)
                    request.session.touch()
                    return response
                else:
                    otp_invalid = True

        request.session.touch()
        return request.render('whatsapp_login.wa_auth_totp_otp_verification_template', {'mobile': mobile,
                                                                                         'otp_sent': otp_sent,
                                                                                         'error': error,
                                                                                         'otp_invalid': otp_invalid})

    @http.route('/web/send/wa-otp', type='http', auth='public', website=True, csrf=True)
    def send_otp(self, **kw):
        if kw.get('country_code') and kw.get('mobile'):
            mobile = kw.get('country_code') + kw.get('mobile')
        else:
            mobile = False
            return request.render('whatsapp_login.wa_otp_login_template', {'invalid_mobile': True})
        user = request.env['res.users'].sudo().search([]).filtered(lambda user: user.partner_id.mobile == mobile.strip('+')) if mobile else False
        # Logic to send OTP to the mobile number
        if user:
            provider_id, whatsapp_template = self.get_config_provider_template()

            if provider_id and whatsapp_template:
                composer = request.env['wa.compose.message'].with_user(provider_id.user_id.id).with_context(
                    default_model=user.partner_id._name,
                    default_res_id=user.partner_id.id,
                    default_template_id=whatsapp_template.id,
                    default_partner_id=user.partner_id.id,
                ).create({})
                composer.send_whatsapp_message()
                return request.render('whatsapp_login.wa_otp_verification_template', {'mobile': '*' * 10 + mobile[10:], 'otp_sent': True})
        else:
            auth_signup = request.env['res.users']._get_signup_invitation_scope()
            if auth_signup == 'b2c':
                provider_id, whatsapp_template = self.get_config_provider_template()
                try:
                    self._send_otp_message_to_public_user(whatsapp_template, provider_id, mobile.strip('+'))
                except Exception as e:
                    _logger.info(_(e))
                return request.render('whatsapp_login.wa_otp_verification_template',
                                      {'mobile': '*' * 10 + mobile[10:], 'otp_sent': True})
            else:
                return request.render('whatsapp_login.wa_otp_login_template', {'number_error': True})

    @http.route('/web/verify/wa-otp', type='http', auth='public', website=True, csrf=True)
    def verify_otp(self, *args, **kw):
        qcontext = request.params.copy()
        session_otp = kw.get('otp')
        user = request.env['res.users'].sudo().search([]).filtered(lambda user: user.partner_id.otp_text == session_otp)
        provider_id, whatsapp_template = self.get_config_provider_template()
        auth_signup = request.env['res.users']._get_signup_invitation_scope()
        if user and (datetime.now() - user.partner_id.otp_time).total_seconds() > (whatsapp_template.otp_expiration_minutes * 60 or 600):
            return request.render('whatsapp_login.wa_otp_verification_template', {'otp_expired': True})
        elif user and user.partner_id.otp_text == session_otp:
            request.env.cr.execute(
                "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                [user.id]
            )
            hashed = request.env.cr.fetchone()[0]
            qcontext.update({'login': user.sudo().login,
                             'name': user.sudo().partner_id.name,
                             'password': hashed})
            request.params.update(qcontext)
            request.session['login_by_whatsapp'] = True
            return self.web_login(*args, **kw)
        elif not user and auth_signup == 'b2c' and request.session.get('otp') == session_otp:
            return request.redirect('/web/signup')
        else:
            # OTP is incorrect, show an error
            return request.render('whatsapp_login.wa_otp_verification_template', {'otp_invalid': True})
        
    
    @http.route('/web/login/wa-otp', type='http', auth='public', website=True, csrf=True)
    def otp_login(self, **kw):
        return request.render('whatsapp_login.wa_otp_login_template', {})

    @http.route('/web/otp/available', type='http', auth='public', website=True, csrf=True)
    def otp_available(self, **kw):
        return request.render('whatsapp_login.wa_otp_verification_template', {'otp_available': True})

    @http.route('/web/whatsapp/reset_password', type='http', auth='public', website=True, sitemap=False)
    def whatsapp_web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_wa_auth_signup_config()

        if not qcontext.get('wa_reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if kw.get('country_code') and kw.get('mobile'):
            mobile = kw.get('country_code') + kw.get('mobile')
            qcontext.update({'mobile': mobile.strip('+')})

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
               if kw.get('country_code') and kw.get('mobile'):
                    mobile = kw.get('country_code') + kw.get('mobile')
                    assert mobile, _("No login provided.")
                    _logger.info(
                        "Password reset attempt for <%s> by user <%s> from %s",
                        mobile, request.env.user.login, request.httprequest.remote_addr)
                    request.env['res.users'].sudo().whatsapp_reset_password(mobile)
                    qcontext['message_sent'] = _("Password reset instructions sent to your whatsapp number")
            except UserError as e:
                qcontext['error'] = e.args[0]
            except Exception as e:
                qcontext['error'] = str(e)

        response = request.render('whatsapp_login.wa_auth_reset_password_template', qcontext)
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    def _prepare_signup_values(self, qcontext):
        qcontext.update(request.params.copy())
        values = super()._prepare_signup_values(qcontext)
        values.update({'mobile': qcontext.get('mobile')})
        return values
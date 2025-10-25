import contextlib
import logging

from ast import literal_eval
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.http import request

from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.addons.auth_signup.models.res_partner import SignupError

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _action_reset_password(self, signup_type="reset"):
        _logger.info("-- _action_reset_password --- called from custom addons when user create first time %s",self.env.context)
        """ create signup token for each user, and send their signup url by email """
        if self.env.context.get('install_mode') or self.env.context.get('import_file'):
            return
        if self.filtered(lambda user: not user.active):
            raise UserError(_("You cannot perform this action on an archived user."))
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))
        self.mapped('partner_id').signup_prepare(signup_type=signup_type)

        # this is added for when user created from alt cart web assign module then skip mail process 
        user_for_cart_assing = bool(self.env.context.get('user_for_cart_assing'))
        if user_for_cart_assing:
            _logger.info("Skipping signup/reset email because user was created from Cart Assigner flow.")
            # self.env['marketing.campaign'].search([('state', '=', 'running')]).sync_participants()
            # self.env['marketing.campaign'].search([('state', '=', 'running')]).execute_activities()

            # Comment 38 to 53 linse on oct 7 

            # custom_cron = self.env['ir.cron'].search([('id','=',105)])
            # _logger.info("------ custom_cron -------- %s",custom_cron)
            # if custom_cron:
            #     _logger.info("if inside custom_cron -------------")
            #     custom_cron.method_direct_trigger()
            
            # if self.env.ref('marketing_automation.ir_cron_campaign_sync_participants'):
            #     self.env.ref('marketing_automation.ir_cron_campaign_sync_participants').method_direct_trigger()

            # if self.env.ref('marketing_automation.ir_cron_campaign_execute_activities'):
            #     self.env.ref('marketing_automation.ir_cron_campaign_execute_activities').method_direct_trigger()

            # if self.env.ref('mass_mailing.ir_cron_mass_mailing_queue'):
            #     self.env.ref('mass_mailing.ir_cron_mass_mailing_queue').method_direct_trigger() 

            # self.env['ir.cron'].browse(105)
            # self.env.ref('marketing_automation.ir_cron_campaign_sync_participants').method_direct_trigger()
            # self.env.ref('marketing_automation.ir_cron_campaign_execute_activities').method_direct_trigger()
            # self.env.ref('mass_mailing.ir_cron_mass_mailing_queue').method_direct_trigger()
            return

        # send email to users with their signup url
        account_created_template = None
        if create_mode:
            account_created_template = self.env.ref('auth_signup.set_password_email', raise_if_not_found=False)
            if account_created_template and account_created_template._name != 'mail.template':
                _logger.error("Wrong set password template %r", account_created_template)
                return

        email_values = {
            'email_cc': False,
            'auto_delete': True,
            'message_type': 'user_notification',
            'recipient_ids': [],
            'partner_ids': [],
            'scheduled_date': False,
        }

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.", user.name))
            email_values['email_to'] = user.email
            with contextlib.closing(self.env.cr.savepoint()):
                if account_created_template:
                    account_created_template.send_mail(
                        user.id, force_send=True,
                        raise_exception=True, email_values=email_values)
                else:
                    user_lang = user.lang or self.env.lang or 'en_US'
                    body = self.env['mail.render.mixin'].with_context(lang=user_lang)._render_template(
                        self.env.ref('auth_signup.reset_password_email'),
                        model='res.users', res_ids=user.ids,
                        engine='qweb_view', options={'post_process': True})[user.id]
                    mail = self.env['mail.mail'].sudo().create({
                        'subject': self.with_context(lang=user_lang).env._('Password reset'),
                        'email_from': user.company_id.email_formatted or user.email_formatted,
                        'body_html': body,
                        **email_values,
                    })
                    mail.send()
            if signup_type == 'reset':
                _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)
                message = _('A reset password link was send by email')
            else:
                _logger.info("Signup email sent for user <%s> to <%s>", user.login, user.email)
                message = _('A signup link was send by email')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Notification',
                'message': message,
                'sticky': False
            }
        }
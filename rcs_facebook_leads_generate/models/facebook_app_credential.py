# -*- coding: utf-8 -*-

import requests
import json
import base64
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from werkzeug.urls import url_encode
import logging

_logger = logging.getLogger(__name__)


class FacebookAppCredentialInfo(models.Model):
    _name = 'facebook.app.credential.info'
    _description = "Facebook App Credential Information"
    _order = 'id desc'
    _rec_name = 'facebook_app_id'

    facebook_app_id = fields.Char(string='App ID', required=True)
    facebook_app_secret = fields.Char(string='App Secret', required=True)
    facebook_user_access_token = fields.Char(string='User Access Token')
    facebook_user_access_token_state = fields.Selection([('valid', 'Valid'), ('invalid', 'Invalid'), ('unknown', 'Unknown')],
                                                        string='Token State', compute='_get_state_of_user_access_token', store=True)
    facebook_user_access_token_state_message = fields.Text(string='Error Message', compute='_get_state_of_user_access_token')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    facebook_page_ids = fields.One2many('facebook.page', 'facebook_app_id', string='Facebook Pages')
    facebook_page_count = fields.Integer(string='Pages', compute='_get_facebook_pages')

    @api.depends('facebook_page_ids')
    def _get_facebook_pages(self):

        for page in self:
            page.facebook_page_count = len(page.facebook_page_ids)

    def action_view_facebook_page(self, pages=False):

        if not pages:
            pages = self.env['facebook.page'].search([('facebook_app_id', '=', self.id)])
        action = self.env['ir.actions.actions']._for_xml_id('rcs_facebook_leads_generate.action_facebook_page')
        if len(pages) > 1:
            action['domain'] = [('id', 'in', pages.ids)]
        elif len(pages) == 1:
            form_view = [(self.env.ref('rcs_facebook_leads_generate.facebook_page_form').id, 'form')]
            action['views'] = form_view
            action['res_id'] = pages.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _facebook_accounts_from_configuration(self, fb_app_id):

        get_base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        redirect_url = "%s/facebook_leads/auth" % get_base_url
        if self.facebook_user_access_token:
            get_base_facebook_url = 'https://graph.facebook.com/v22.0/oauth/access_token?%s'
            get_params = {
                'grant_type': "fb_exchange_token",
                'client_id': fb_app_id,
                'client_secret': self.facebook_app_secret,
                'fb_exchange_token': self.facebook_user_access_token
            }
            url = get_base_facebook_url % url_encode(get_params)
            payload = ""
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            _logger.info('User Access Token: %r', response.text)
            access_token = json.loads(response.text).get('access_token')
            return self.write({'facebook_user_access_token': access_token})
        else:
            get_base_facebook_url = 'https://www.facebook.com/v22.0/dialog/oauth?%s'
            get_params = {
                'client_id': fb_app_id,
                'redirect_uri': redirect_url,
                'response_type': 'token',
                'scope': ','.join([
                    'pages_manage_ads',
                    'pages_manage_metadata',
                    'pages_read_engagement',
                    'pages_read_user_content',
                    'pages_manage_engagement',
                    'ads_management',
                    'pages_manage_posts',
                    'read_insights',
                    'pages_show_list',
                    'leads_retrieval'
                ])
            }
            return {
                'type': 'ir.actions.act_url',
                'url': get_base_facebook_url % url_encode(get_params),
                'target': 'new'
            }

    def action_get_facebook_access_token(self):

        self.ensure_one()
        if self.facebook_app_id and self.facebook_app_secret:
            return self._facebook_accounts_from_configuration(self.facebook_app_id)
        else:
            raise UserError(_("You are Missing App ID and App Secret."))

    @api.depends('facebook_user_access_token')
    def _get_state_of_user_access_token(self):

        if not self.facebook_user_access_token:
            self.facebook_user_access_token_state = 'invalid'
            self.facebook_user_access_token_state_message = 'No Access Token provided'
        if not (self.facebook_app_id and self.facebook_app_secret):
            self.facebook_user_access_token_state = 'unknown'
            self.facebook_user_access_token_state_message = 'App ID and App Secret are required to debug access token'
            return
        response = requests.get("https://graph.facebook.com/v22.0/debug_token", params={
            'input_token': self.facebook_user_access_token,
            'access_token': '|'.join([self.facebook_app_id, self.facebook_app_secret])
        }).json()
        if response.get('error') or response.get('data', []).get('error'):
            self.facebook_user_access_token_state = 'invalid'
            self.facebook_user_access_token_state_message = response.get('error') and response['error']['message'] or \
                                                            response['data']['error']['message']
            return
        if not response['data']['is_valid']:
            self.facebook_user_access_token_state = 'invalid'
            return
        if response['data']['type'] != 'USER':
            self.facebook_user_access_token_state = 'invalid'
            self.facebook_user_access_token_state_message = 'Token is of type %s. Must be of type USER' % (
                response['data']['type'])
            return
        scopes = response['data']['scopes']
        if any([scope not in scopes for scope in
                ('leads_retrieval', 'pages_manage_ads', 'pages_read_engagement', 'ads_management')]):
            self.facebook_user_access_token_state = 'invalid'
            self.facebook_user_access_token_state_message = 'Missing permissions: %s' % (', '.join(
                [scope for scope in ('leads_retrieval', 'pages_manage_ads', 'pages_read_engagement', 'ads_management')
                 if scope not in scopes]))
            return
        self.facebook_user_access_token_state = 'valid'
        self.facebook_user_access_token_state_message = ''

    def action_get_facebook_pages(self):

        response = requests.get("https://graph.facebook.com/me/accounts", params={
            'access_token': self.facebook_user_access_token,
            'fields': 'id,category_list,category,contact_address,cover,rating_count,about,access_token,followers_count,name,description'
        }).json()
        if not response:
            raise UserError(_("Not Data Found.."))
        _logger.info('Pages: %r', response.get('data'))
        if response.get('error'):
            raise ValidationError(response['error']['message'])
        if not response.get('data'):
            return

        for page in response['data']:
            for category in page.get('category_list'):
                category_id = self.env['facebook.page.category.info'].search([('name', '=', category.get('name'))])
                if not category_id:
                    self.env['facebook.page.category.info'].create({
                        'category_id': category.get('id'),
                        'name': category.get('name')
                    })
            category_id = self.env['facebook.page.category.info'].search([('name', '=', page.get('category'))]).id
            page_id = self.env['facebook.page'].search([('facebook_page_id', '=', page.get('id'))])
            if page_id:
                page_id.write({
                    'name': page.get('name'),
                    'facebook_app_id': self.id,
                    'facebook_page_id': page.get('id'),
                    'page_access_token': page.get('access_token'),
                    'rating_count': str(page.get('rating_count', 0)),
                    'follower_count': page.get('followers_count'),
                    'description': page.get('description'),
                    'about': page.get('about'),
                    'category_id': category_id,
                })
            else:
                page_id = self.env['facebook.page'].create({
                    'name': page.get('name'),
                    'facebook_app_id': self.id,
                    'facebook_page_id': page.get('id'),
                    'page_access_token': page.get('access_token'),
                    'rating_count': str(page.get('rating_count', 0)),
                    'follower_count': page.get('followers_count'),
                    'description': page.get('description'),
                    'about': page.get('about'),
                    'category_id': category_id,
                })
            url = page.get('cover').get('source')
            if url:
                img = base64.b64encode(requests.get(url.strip()).content).replace(b"\n", b"")
                page_id.write({'cover': img})
        action = self.env.ref('rcs_facebook_leads_generate.action_facebook_page').read()[0]
        return action

    def get_access_token(self):

        credential_obj = self.search([])
        for app in credential_obj:
            app.action_get_facebook_access_token()

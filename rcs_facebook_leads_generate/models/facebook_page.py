# -*- coding: utf-8 -*-

import requests
import logging
from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models,_

_logger = logging.getLogger(__name__)


class FacebookPage(models.Model):
    _name = 'facebook.page'
    _description = ("Facebook Page"
                    "")
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(string='Page Name')
    facebook_app_id = fields.Many2one('facebook.app.credential.info', string='Facebook App ID')
    facebook_page_id = fields.Char(string='Page ID', required=True)
    page_access_token = fields.Char(string='Page Access Token', required=True)
    form_ids = fields.One2many('facebook.form.info', 'facebook_page_id', string='Lead Forms')
    description = fields.Text(string='Description')
    category_id = fields.Many2one('facebook.page.category.info', string='Category')
    cover = fields.Binary()
    rating_count = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    follower_count = fields.Char(string='Follower Count')
    about = fields.Char(string='About')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    form_count = fields.Integer(string="Forms", compute='_get_facebook_lead_forms_count')
    facebook_lead_count = fields.Integer(string="Leads", compute='_get_facebook_lead_forms_count')

    @api.depends('name', 'page_id')
    def name_get(self):

        result = []
        for page in self:
            name = page.name if page.name else page.page_id
            result.append((page.id, name))
        return result

    @api.depends('form_ids', 'form_ids.lead_count')
    def _get_facebook_lead_forms_count(self):

        for page in self:
            page.facebook_lead_count = sum(page.form_ids.mapped('lead_count'))
            page.form_count = len(page.form_ids)

    def action_view_forms(self, forms=False):

        if not forms:
            forms = self.form_ids
        action = self.env['ir.actions.actions']._for_xml_id('rcs_facebook_leads_generate.action_facebook_form')
        if len(forms) > 1:
            action['domain'] = [('id', 'in', forms.ids)]
        elif len(forms) == 1:
            form_view = [(self.env.ref('rcs_facebook_leads_generate.facebook_form_form').id, 'form')]
            action['views'] = form_view
            action['res_id'] = forms.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def facebook_form_processing(self, response):

        if not response.get('data'):
            return
        for form in response['data']:
            if self.form_ids.filtered(
                    lambda f: f.facebook_form_id == form['id']):
                continue
            if form['status'] == 'ACTIVE':
                self.env['facebook.form.info'].create({
                    'name': form['name'],
                    'facebook_form_id': form['id'],
                    'facebook_page_id': self.id}).get_facebook_lead_fields()

        if response.get('paging') and response['paging'].get('next'):
            self.facebook_form_processing(requests.get(response['paging']['next']).json())
        return

    def action_get_forms(self):

        response = requests.get("https://graph.facebook.com/v22.0/" + self.facebook_page_id + "/leadgen_forms", params={
            'access_token': self.page_access_token
        }).json()
        if not response:
            raise UserError(_("Not Data Found.."))
        _logger.info('Forms: %r', response.get('data'))
        if response.get('error'):
            raise ValidationError(response['error']['message'])
        self.facebook_form_processing(response)
        action = self.env.ref('rcs_facebook_leads_generate.action_facebook_form').read()[0]
        return action


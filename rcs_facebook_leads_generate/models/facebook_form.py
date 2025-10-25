# -*- coding: utf-8 -*-

import requests
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class FacebookForm(models.Model):
    _name = 'facebook.form.info'
    _description = "Facebook Form Information"
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(required=True)
    facebook_form_id = fields.Char(required=True, string='Facebook Form ID')
    facebook_page_access_token = fields.Char(required=True, related='facebook_page_id.page_access_token', string='Facebook Page Access Token')
    facebook_page_id = fields.Many2one('facebook.page', readonly=True, ondelete='cascade', string='Facebook Page')
    mappings = fields.One2many('facebook.form.field.info', 'facebook_form_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    team_id = fields.Many2one('crm.team', domain=['|', ('use_leads', '=', True), ('use_opportunities', '=', True)],
                              string="Sales Team")
    campaign_id = fields.Many2one('utm.campaign')
    source_id = fields.Many2one('utm.source')
    medium_id = fields.Many2one('utm.medium')
    lead_ids = fields.One2many('crm.lead', 'facebook_form_id', string="leads", compute='_get_facebook_leads', copy=False)
    lead_count = fields.Integer(string="Leads", compute='_get_facebook_leads')
    won_lead = fields.Integer(string="Won Lead", compute='_get_facebook_leads')
    lost_lead = fields.Integer(string="Lost Leads", compute='_get_facebook_leads')

    @api.depends('lead_ids')
    def _get_facebook_leads(self):

        for form in self:
            leads = self.env['crm.lead'].search(
                [('facebook_form_id', '=', form.id), '|', ('active', '=', True), ('active', '=', False)])
            form.lead_ids = leads
            form.lead_count = len(leads)
            form.won_lead = len(leads.filtered(lambda l: l.stage_id.is_won == True and l.active != False))
            form.lost_lead = len(leads.filtered(lambda l: l.active == False))

    def action_view_fb_leads(self, leads=False):

        if not leads:
            leads = self.mapped('lead_ids')
        action = self.env['ir.actions.actions']._for_xml_id('crm.crm_lead_all_leads')
        if len(leads) > 1:
            action['domain'] = [('id', 'in', leads.ids)]
        elif len(leads) == 1:
            form_view = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]
            action['views'] = form_view
            action['res_id'] = leads.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_won_leads(self, won_leads=False):

        if not won_leads:
            won_leads = self.mapped('lead_ids').filtered(
                lambda wl: wl.stage_id.is_won == True and wl.active == True)
        action = self.env['ir.actions.actions']._for_xml_id('crm.crm_lead_all_leads')
        if len(won_leads) > 1:
            action['domain'] = [('id', 'in', won_leads.ids)]
        elif len(won_leads) == 1:
            form_view = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]
            action['views'] = form_view
            action['res_id'] = won_leads.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_view_lost_leads(self, lost_leads=False):

        if not lost_leads:
            lost_leads = self.env['crm.lead'].search(
                [('facebook_form_id', '=', self.id), '&', ('active', '=', False), ('probability', '=', 0)])
        action = self.env['ir.actions.actions']._for_xml_id('crm.crm_lead_all_leads')
        action['context'] = {'search_default_lost': 1}
        if len(lost_leads) > 1:
            action['domain'] = [('id', 'in', lost_leads.ids)]
        elif len(lost_leads) == 1:
            form_view = [(self.env.ref('crm.crm_lead_view_form').id, 'form')]
            action['views'] = form_view
            action['res_id'] = lost_leads.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def get_facebook_lead_fields(self):

        self.mappings.unlink()
        response = requests.get("https://graph.facebook.com/v22.0/" + self.facebook_form_id, params={
            'access_token': self.facebook_page_access_token,
            'fields': 'id,created_time,expired_leads_count,leads_count,locale,name,organic_leads_count,page,page_id,'
                      'question_page_custom_headline,questions,status'
        }).json()
        if not response:
            raise UserError(_("Not Data Found.."))
        _logger.info('Fields: %r', response.get('data'))
        self.lead_count = response.get('leads_count')
        if response.get('error'):
            raise ValidationError(response['error']['message'])
        if response.get('questions'):
            for question in response.get('questions'):
                self.env['facebook.form.field.info'].create({
                    'facebook_form_id': self.id,
                    'name': question['label'],
                    'facebook_field': question['key'],
                    'odoo_field': self.env['facebook.form.mapping'].search(
                        [('facebook_field', '=', question['key'])], limit=1) and self.env[
                                      'facebook.form.mapping'].search([('facebook_field', '=', question['key'])],
                                                                      limit=1).odoo_field.id or ''
                })

    def action_guess_mapping(self):

        for rec in self:
            rec.mappings.action_guess_mapping()

    def action_fetch_leads_from_facebook(self):

        fb_api = "https://graph.facebook.com/v22.0/"
        response = requests.get(fb_api + self.facebook_form_id + "/leads", params={
            'access_token': self.facebook_page_access_token,
            'fields': 'campaign_id, field_data, created_time, is_organic, ad_id, campaign_name, adset_name, ad_name, adset_id'
        }).json()
        if not response:
            raise UserError(_("Not Data Found.."))
        _logger.info('Leads: %r', response.get('data'))
        if response.get('error'):
            _logger.info('Fetch of leads has error: %r', response['error']['message'])
        self.lead_ids.facebook_lead_processing(response, self)
        _logger.info('Fetch of leads has ended')

    def facebook_leads(self):

        for form in self.browse(self.env.context['active_ids']):
            form.action_fetch_leads_from_facebook()

    def my(self):
        return self.env['facebook.page'].action_view_forms()

    # def action_view_forms(self):
    #     return {
    #         'name': _('Lead Form'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'facebook.form.info',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('rcs_facebook_leads_generate.facebook_form_form').id,
    #         'target': '_blank',
    #         'res_id': self.id,
    #     }
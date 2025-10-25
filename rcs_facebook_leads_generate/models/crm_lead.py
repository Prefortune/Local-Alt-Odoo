# -*- coding: utf-8 -*-

import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    facebook_lead_id = fields.Char(readonly=True)
    facebook_page_id = fields.Many2one('facebook.page', related='facebook_form_id.facebook_page_id', store=True, readonly=True)
    facebook_form_id = fields.Many2one('facebook.form.info', readonly=True)
    facebook_ad_set_id = fields.Many2one('utm.adset.info', readonly=True)
    facebook_ad_id = fields.Many2one('utm.medium', related='medium_id', store=True, readonly=True, string='Fb Ad')
    facebook_campaign_id = fields.Many2one('utm.campaign', related='campaign_id', store=True, readonly=True,
                                           string='Facebook Campaign')
    facebook_date_create = fields.Datetime(readonly=True)
    facebook_is_organic = fields.Boolean(readonly=True)

    _sql_constraints = [
        ('facebook_lead_unique', 'unique(facebook_lead_id)', 'This Facebook lead already exists!')
    ]

    def get_facebook_ad(self, lead):

        utm_medium_obj = self.env['utm.medium']
        if not lead.get('ad_id'):
            return utm_medium_obj
        if not utm_medium_obj.search([('facebook_ad_id', '=', lead['ad_id'])]):
            return utm_medium_obj.create({
                'facebook_ad_id': lead['ad_id'],
                'name': lead['ad_name'],
            }).id
        return utm_medium_obj.search([('facebook_ad_id', '=', lead['ad_id'])], limit=1)[0].id

    def get_facebook_adset(self, lead):

        utm_adset_obj = self.env['utm.adset.info']
        if not lead.get('adset_id'):
            return utm_adset_obj
        if not utm_adset_obj.search([('facebook_adset_id', '=', lead['adset_id'])]):
            return utm_adset_obj.create({
                'facebook_adset_id': lead['adset_id'],
                'name': lead['adset_name']
            }).id
        return utm_adset_obj.search([('facebook_adset_id', '=', lead['adset_id'])], limit=1)[0].id

    def get_facebook_campaign(self, lead):

        utm_campaign_obj = self.env['utm.campaign']
        if not lead.get('campaign_id'):
            return utm_campaign_obj
        if not utm_campaign_obj.search([('facebook_campaign_id', '=', lead['campaign_id'])]):
            return utm_campaign_obj.create({
                'facebook_campaign_id': lead['campaign_id'],
                'name': lead['campaign_name'],
            }).id
        return utm_campaign_obj.search([('facebook_campaign_id', '=', lead['campaign_id'])], limit=1)[0].id

    def prepare_facebook_lead_creation_data(self, lead, form):

        vals, notes = self.get_fields_from_data(lead, form)
        vals.update({
            'facebook_lead_id': lead['id'],
            'facebook_is_organic': lead['is_organic'],
            'name': self.get_opportunity_name_from_lead(vals, lead, form),
            'description': "\n".join(notes),
            'team_id': form.team_id and form.team_id.id,
            'facebook_campaign_id': form.campaign_id and form.campaign_id.id or self.get_facebook_campaign(lead),
            'source_id': form.source_id and form.source_id.id,
            'medium_id': form.medium_id and form.medium_id.id or self.get_facebook_ad(lead),
            'user_id': form.team_id and form.team_id.user_id and form.team_id.user_id.id or False,
            'facebook_ad_set_id': self.get_facebook_adset(lead),
            'facebook_form_id': form.id,
            'facebook_date_create': lead['created_time'].split('+')[0].replace('T', ' ')
        })
        return vals

    def facebook_lead_creation(self, lead, form):

        vals = self.prepare_facebook_lead_creation_data(lead, form)
        return self.create(vals)

    def get_opportunity_name_from_lead(self, vals, lead, form):

        if not vals.get('name'):
            vals['name'] = '%s - %s' % (form.name, lead['id'])
        return vals['name']

    def get_fields_from_data(self, lead, form):

        vals, notes = {}, []
        form_mapping = form.mappings.filtered(lambda m: m.odoo_field).mapped('facebook_field')
        unmapped_fields = []
        for name, value in lead.items():
            unmapped_fields.append((name, value))
            if name not in form_mapping:
                continue
            odoo_field = form.mappings.filtered(lambda m: m.facebook_field == name).odoo_field
            if odoo_field.ttype == 'many2one':
                related_value = self.env[odoo_field.relation].search([('name', '=ilike', value)])
                if related_value:
                    vals.update({odoo_field.name: related_value and related_value.id})
            elif odoo_field.ttype in ('float', 'monetary'):
                vals.update({odoo_field.name: float(value)})
            elif odoo_field.ttype == 'integer':
                vals.update({odoo_field.name: int(value)})
            elif odoo_field.ttype in ('date', 'datetime'):
                vals.update({odoo_field.name: value.split('+')[0].replace('T', ' ')})
            elif odoo_field.ttype == 'selection':
                vals.update({odoo_field.name: value})
            elif odoo_field.ttype == 'boolean':
                vals.update({odoo_field.name: value == 'true' if value else False})
            else:
                vals.update({odoo_field.name: value})

        for name, value in unmapped_fields:
            if name not in ['created_time', 'is_organic', 'id']:
                notes.append('<b>%s</b>: %s <br><br>' % (str(name.capitalize().replace("_", " ")), value))

        return vals, notes

    def process_field_data_from_lead(self, lead):

        field_data = lead.pop('field_data')
        lead_data = dict(lead)
        lead_data.update([(l['name'], l['values'][0]) for l in field_data if l.get('name') and l.get('values')])
        return lead_data

    def facebook_lead_processing(self, r, form):

        if not r.get('data'):
            return
        for lead in r['data']:
            lead = self.process_field_data_from_lead(lead)
            if not self.search([
                ('facebook_lead_id', '=', lead.get('id')), '|', ('active', '=', True), ('active', '=', False)]):
                opportunity = self.facebook_lead_creation(lead, form)
                if opportunity.contact_name:
                    opportunity.write({
                        'name': opportunity.contact_name
                    })
        try:
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()

        if r.get('paging') and r['paging'].get('next'):
            _logger.info('Fetching leads in Form: %s' % form.name)
            self.facebook_lead_processing(requests.get(r['paging']['next']).json(), form)
        return

    @api.model
    def get_facebook_leads(self):

        fb_api = "https://graph.facebook.com/v22.0/"
        for form in self.env['facebook.form.info'].search([]):
            _logger.info('Start fetch leads from Form: %s' % form.name)
            vals = {
                'access_token': form.facebook_page_access_token,
                'fields': 'campaign_id, field_data, created_time, is_organic, ad_id, campaign_name, adset_name, ad_name, adset_id'
            }
            response = requests.get(fb_api + form.facebook_form_id + "/leads", params=vals).json()
            _logger.info('Leads: %r', response.get('data'))
            if response.get('error'):
                _logger.info('Leads fetch has error: %r', response['error']['message'])
            self.facebook_lead_processing(response, form)
        _logger.info('Leads fetch has ended')

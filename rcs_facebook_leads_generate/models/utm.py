# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class UtmMedium(models.Model):
    _inherit = 'utm.medium'

    facebook_ad_id = fields.Char("Ad ID")

    _sql_constraints = [
        ('facebook_ad_unique', 'unique(fb_ad_id)', 'Checking the duplication of facebook ads!')
    ]


class UtmAdset(models.Model):
    _name = 'utm.adset.info'
    _description = 'Utm Adset Information'
    _rec_name = 'name'

    name = fields.Char()
    facebook_adset_id = fields.Char("Adset ID")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('facebook_adset_unique', 'unique(facebook_adset_id)', 'Checking the duplication of Facebook AdSet already!')
    ]   


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'

    facebook_campaign_id = fields.Char("Facebook Campaign Id")

    _sql_constraints = [
        ('facebook_campaign_unique', 'unique(facebook_campaign_id)', 'This Facebook Campaign already exists!')
    ]

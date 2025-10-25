# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmTeamInherit(models.Model):
    _inherit = 'crm.team'

    last_set_lead_user = fields.Many2one('res.users', string='Last Set Lead User')

    @api.onchange('member_ids')
    def onchange_last_set_lead_user(self):
        for rec in self:
            if rec.last_set_lead_user:
                if rec.last_set_lead_user.id not in rec.member_ids.ids:
                    rec.last_set_lead_user = False

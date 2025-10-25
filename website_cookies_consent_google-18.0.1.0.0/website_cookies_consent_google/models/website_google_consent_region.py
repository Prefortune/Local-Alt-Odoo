# Copyright © 2024 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/15.0/legal/licenses.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WebsiteGoogleConsentRegion(models.Model):
    _name = "website.google.consent.region"
    _description = 'Google Consent Mode Regions'

    country_id = fields.Many2one(comodel_name='res.country', required=True)
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        domain="[('country_id', '=', country_id)]",
    )

    @api.constrains('country_id', 'state_id')
    def _check_unique(self):
        for region in self:
            if self.search_count([
                ('country_id', '=', region.country_id.id),
                ('state_id', '=', region.state_id.id),
            ]) > 1:
                raise ValidationError(_('The Google Consent region must be unique per country and state.'))

    @api.depends('country_id', 'state_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s%s" % (rec.country_id.code, f"-{rec.state_id.code}" if rec.state_id else "")

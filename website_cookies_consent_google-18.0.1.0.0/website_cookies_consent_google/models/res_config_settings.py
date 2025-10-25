# Copyright © 2024 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_google_consent_ads_data_redaction = fields.Boolean(
        related='website_id.google_consent_ads_data_redaction',
        string='Ads Data Redaction',
        readonly=False,
    )
    website_google_consent_url_passthrough = fields.Boolean(
        related='website_id.google_consent_url_passthrough',
        string='URL Passthrough',
        readonly=False,
    )

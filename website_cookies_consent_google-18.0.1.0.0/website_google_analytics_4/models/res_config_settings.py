# Copyright © 2021 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ga4_debug_mode = fields.Boolean(
        related='website_id.ga4_debug_mode',
        readonly=False,
    )
    gtag_tracking_key = fields.Char(
        related='website_id.gtag_tracking_key',
        readonly=False,
    )

    @api.depends('website_id')
    def _compute_has_google_gtag(self):
        self.has_google_gtag = bool(self.gtag_tracking_key)

    def _inverse_has_google_gtag(self):
        if not self.has_google_gtag:
            self.gtag_tracking_key = False

    has_google_gtag = fields.Boolean(
        string='Google Tag (gtag.js)',
        compute=_compute_has_google_gtag,
        inverse=_inverse_has_google_gtag,
    )

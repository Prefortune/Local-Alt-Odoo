# Copyright © 2021 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html).

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    ga4_debug_mode = fields.Boolean(string='Debug Mode')
    gtag_tracking_key = fields.Char(string='Tag ID')

    def _gtag_params(self):
        """ Return additional parameters for the Google Tag. Method to override. """
        self.ensure_one()
        return {'debug_mode': True} if self.ga4_debug_mode else {}

    def _gtag_configs(self):
        self.ensure_one()
        return [{
            'key': self.gtag_tracking_key or '',
            'params': self._gtag_params(),
        }]

    def gtag_get_primary_key(self):
        self.ensure_one()
        return self.gtag_tracking_key or ''

    def gtag_get_source_url(self):
        self.ensure_one()
        return f"https://www.googletagmanager.com/gtag/js?id={self.gtag_get_primary_key()}"

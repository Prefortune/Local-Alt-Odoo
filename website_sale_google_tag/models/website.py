# Copyright © 2024 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/17.0/legal/licenses.html).

from odoo import models


class Website(models.Model):
    _inherit = "website"

    def gtm_get_key(self):
        super(Website, self).gtm_get_key()
        gtm_service = self.sudo().tracking_service_ids.filtered(lambda sv: sv.type == 'gtm' and sv.active)
        return gtm_service[0].key if gtm_service else ''

# Copyright © 2022 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License OPL-1 (https://www.odoo.com/documentation/14.0/legal/licenses.html).

from odoo import fields, models

FB_STATUSES = [('active', 'Active'), ('archived', 'Archived')]


class ProductProduct(models.Model):
    _inherit = "product.product"

    feed_fb_status = fields.Selection(
        selection=FB_STATUSES,
        default='active',
        string='Status',
    )

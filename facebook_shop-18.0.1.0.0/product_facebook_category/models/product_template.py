# Copyright © 2021 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    facebook_category_id = fields.Many2one(
        comodel_name='product.facebook.category',
        string='Facebook Category',
    )

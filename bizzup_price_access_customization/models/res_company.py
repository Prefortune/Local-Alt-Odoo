# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"
    """Inherited the res company for adding the new field"""

    is_main = fields.Boolean(string="Is Main?", copy=False)

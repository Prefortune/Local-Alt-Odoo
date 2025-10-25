# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class FacebookPageCategoryInfo(models.Model):
    _name = 'facebook.page.category.info'
    _description = "Facebook Category Information"
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(string='Category Name' , required=True)
    category_id = fields.Char(string="Category ID")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Page Category Name is Unique')
    ]

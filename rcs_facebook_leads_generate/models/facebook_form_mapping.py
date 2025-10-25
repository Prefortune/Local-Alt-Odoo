# -*- coding: utf-8 -*-

from odoo import api, fields, models


class FacebookFormMapping(models.Model):
    _name = 'facebook.form.mapping'
    _description = 'Default field mapping for new forms'
    _order = 'id desc'

    odoo_field = fields.Many2one('ir.model.fields', ondelete='cascade', required=True, domain=[
        ('model', '=', 'crm.lead'), ('store', '=', True), ('readonly', '=', False),
        ('ttype', 'in', ('char', 'date', 'datetime', 'float', 'html', 'integer', 'monetary', 'many2one', 'selection',
                         'phone', 'text'))],
    )
    facebook_field = fields.Char(required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('map_unique', 'unique(odoo_field, facebook_field)', 'Default Mapping must be unique')
    ]

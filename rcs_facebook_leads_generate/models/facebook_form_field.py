# -*- coding: utf-8 -*-

from odoo import api, fields, models,_


class FacebookFormFieldInfo(models.Model):
    _name = 'facebook.form.field.info'
    _description = 'Facebook form fields'
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char()
    facebook_form_id = fields.Many2one('facebook.form.info', required=True, ondelete='cascade', string='Form')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    odoo_field = fields.Many2one('ir.model.fields', ondelete='set null', required=False, domain=[
        ('model', '=', 'crm.lead'), ('store', '=', True),
        ('ttype', 'in', ('char', 'date', 'datetime', 'float', 'html', 'integer', 'monetary', 'many2one', 'selection',
                         'phone', 'text'))],
    )
    facebook_field = fields.Char(required=True)

    _sql_constraints = [
        ('field_unique', 'unique(facebook_form_id, odoo_field, facebook_field)', 'Mapping must be unique per form')
    ]

    def action_guess_mapping(self):

        for rec in self:
            mapping = self.env['facebook.form.mapping'].search([('facebook_field', '=', rec.facebook_field)], limit=1)
            if mapping:
                rec.odoo_field = mapping.odoo_field

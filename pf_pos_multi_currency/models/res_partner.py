from odoo import models,fields,api,_
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.constrains('name')
    def _check_name_unique(self):
        for partner in self:
            if self.env['res.partner'].search_count([
                ('name', '=', partner.name),
                ('id', '!=', partner.id),
                ('active', '=', True),
            ]) > 0:
                raise ValidationError(_('A contact with this name already exists!'))

    _sql_constraints = [
        ('check_name', "CHECK( (type='contact' AND name IS NOT NULL) or (type!='contact') )", 'Contacts require a name'),
        ('uniq_name', 'unique(name)', 'Name must be unique!'),
    ]


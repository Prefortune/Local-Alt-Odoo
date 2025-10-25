from odoo import api, fields, models, tools, _
from odoo.osv.expression import AND
from random import randint

class PosOrder(models.Model):
    _name = "pf.order.tag"
    _description="Order Tags"

    def _pf_get_color(self):
        return randint(1, 11)


    name = fields.Char('Tag Name', required=True, translate=True)
    color = fields.Integer('Color', default=_pf_get_color)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]



# -*- coding: utf-8 -*-

from odoo import fields, models, api


class DeliveryRoute(models.Model):
    _name = "delivery.route"
    _description = "Delivery Route"

    _rec_name = "name"

    code = fields.Char(string="Code", required=True)

    # set code will be unique
    _sql_constraints = [("unique_code", "unique(code)", "code will be unique")]

    name = fields.Char("Name", required=True)

    @api.depends("code", "name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = "%s, %s" % (record.code, record.name)

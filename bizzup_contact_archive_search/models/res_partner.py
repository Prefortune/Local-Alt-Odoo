# -*- coding: utf-8 -*-

import re
from odoo.osv import expression
from odoo import models, fields, api
from odoo.service.security import check


class ResPartner(models.Model):
    """Inherited SaleOrder for customization."""

    _inherit = "res.partner"

    same_mobile_partner_id = fields.Many2one(
        "res.partner", string="Partner with same mobile number", readonly=True
    )

    cust_mobile_partner = fields.Char('Custom Mobile',  compute='_compute_custom_mobile', store=True,)
    cust_phone_partner = fields.Char('Custom Phone', compute='_compute_custom_phone',store=True)


    @api.depends('phone')
    def _compute_custom_phone(self):
        for partner in self:
            # If the partner has a phone and it's not False or None
            if partner.phone:
                partner.cust_phone_partner = re.sub(r'\D', '', partner.phone)  # Removes non-numeric characters
            else:
                partner.cust_phone_partner = False  # If there's no phone, clear the field

    @api.depends('mobile')
    def _compute_custom_mobile(self):
        for partner in self:
            # If the partner has a mobile and it's not False or None
            if partner.mobile:
                partner.cust_mobile_partner = re.sub(r'\D', '', partner.mobile)  # Removes non-numeric characters
            else:
                partner.cust_mobile_partner = False  # If there's no mobile, clear the field

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if "mobile" in vals:
            partner = self.env["res.partner"].search(
                [("mobile", "=", vals.get("mobile")), ("id", "!=", self.id)],
                limit=1
            )
            if partner:
                self.same_mobile_partner_id = partner.id
            else:
                self.same_mobile_partner_id = False
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if res.mobile:
            partner = self.env["res.partner"].search(
                [("mobile", "=", res.mobile), ("id", "!=", res.id)], limit=1
            )
            if partner:
                res.same_mobile_partner_id = partner.id
            else:
                res.same_mobile_partner_id = False
        return res

    @api.onchange("mobile")
    def onchange_mobile(self):
        """this method help to check duplicat mobile number and show
        warning"""
        if self.mobile:
            partner = self.env["res.partner"].search(
                [("mobile", "=", self.mobile), ("id", "!=", self.id)], limit=1
            )
            if partner:
                self.same_mobile_partner_id = partner.id
            else:
                self.same_mobile_partner_id = False

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = []
        domain = args or []
        if name:
            domain_mobile_phone = expression.AND([
                domain, ['|','|','|',
                    ('vat',operator, name),
                    ('mobile',operator,name),
                    ('phone_sanitized',operator,name),
                    ('cust_phone_partner',operator,name),# Search in sanitized phone field
                ]
            ])

            partners = self.search(domain_mobile_phone, limit=limit)
            result.extend((partner.id, partner.display_name) for partner in partners.sudo())
            domain = expression.AND([domain, [('id', 'not in', partners.ids)]])

            if limit is not None:
                limit -= len(partners)
                if limit <= 0:
                    return result

        result.extend(super().name_search(name, domain, operator, limit))
        return result

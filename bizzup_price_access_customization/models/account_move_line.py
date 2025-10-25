# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    """Inherited the account move for customization of the price unit
        based on the groups"""
    _inherit = "account.move.line"

    is_group = fields.Boolean(
        string="Is Group",
        copy=False,
        compute="_compute_is_group"
    )

    @api.depends("name")
    def _compute_is_group(self):
        """Method to check the price groups"""
        for rec in self:
            rec.is_group = False
            if not self.env.user.has_groups("bizzup_price_access_customization.group_bpac_change_docs"):
                rec.is_group = True

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        for rec in self:
            if rec.product_id and rec.price_unit != rec.product_id.list_price and rec.move_id.move_type in ['out_invoice', 'out_refund']:
                # Check if the boolean field is True, disallow editing the product price (Invoices)
                if self.env.user.company_id.is_main and not self.env.user.has_group("bizzup_price_access_customization.group_bpac_change_docs"):
                    raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")
                elif not self.env.user.company_id.is_main and rec.product_id.create_uid.company_id.is_main:
                    raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")
                elif not self.env.user.company_id.is_main and not rec.product_id.create_uid.company_id.is_main and not self.env.user.has_group("bizzup_price_access_customization.group_bpac_change_docs"):
                    raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")
            if rec.product_id and rec.price_unit != rec.product_id.standard_price and rec.move_id.move_type in ['in_invoice', 'in_refund']:
                # Check if the boolean field is True, disallow editing the product price (Bills)
                if self.env.user.company_id.is_main and not self.env.user.has_group("bizzup_price_access_customization.group_bpac_change_docs"):
                    raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")
                elif not self.env.user.company_id.is_main and rec.product_id.create_uid.company_id.is_main:
                    raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")
                elif not self.env.user.company_id.is_main and not rec.product_id.create_uid.company_id.is_main and not self.env.user.has_group("bizzup_price_access_customization.group_bpac_change_docs"):
                    raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")

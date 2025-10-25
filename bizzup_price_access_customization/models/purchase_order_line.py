# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    """Inherited the purchase order for customization of the price unit
        based on the groups"""
    _inherit = "purchase.order.line"

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
            if rec.product_id and rec.price_unit and rec.price_unit != rec.product_id.standard_price and rec.price_unit != rec.product_id.standard_price:
                # Check if the boolean field is True, disallow editing the product price
                if self.env.user.company_id.is_main and not self.env.user.has_group("bizzup_price_access_customization.group_bpac_change_docs"):
                    raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")
                elif not self.env.user.company_id.is_main and rec.product_id.create_uid.company_id.is_main:
                    raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")
                elif not self.env.user.company_id.is_main and not rec.product_id.create_uid.company_id.is_main and not self.env.user.has_group("bizzup_price_access_customization.group_bpac_change_docs"):
                    raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")

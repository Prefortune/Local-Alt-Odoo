# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def create(self, vals_list):
        """Method to restrict edit the records based on the company boolean"""
        res = super(ProductPricelist, self).create(vals_list)
        if not self.env.user.company_id.is_main:
            raise ValidationError(
                " שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך."
                )
        return res

    def write(self, vals_list):
        """Method to restrict edit the records based on the company boolean"""
        res = super(ProductPricelist, self).write(vals_list)
        if not self.env.user.company_id.is_main:
            raise ValidationError(
                " שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך."
                )
        return res

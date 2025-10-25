# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    """Inherited the sale order for customization of the price unit
        based on the groups"""
    _inherit = "sale.order.line"

    is_group = fields.Boolean(
        string="Is Group",
        copy=False,
        compute="_compute_is_group"
    )

    def _compute_is_group(self):
        """Method to check the price groups"""
        for rec in self:
            rec.is_group = False
            if not self.env.user.has_groups("bizzup_price_access_customization.group_bpac_change_docs"):
                rec.is_group = True

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        for rec in self:
            if rec.product_id:
                product = rec.product_id
                pricelist_lines = self.env['product.pricelist.item'].search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id)  # Match the product
                ])
                pricelist_prices = pricelist_lines.mapped('fixed_price')  # Assuming 'fixed_price' contains the price
                price_comparison_list = pricelist_prices + [product.list_price]
                if rec.price_unit not in price_comparison_list:
                    # Check if the boolean field is True, disallow editing the product price
                    if self.env.user.company_id.is_main and not self.env.user.has_group("bizzup_price_access_customization.group_bpac_change_docs"):
                        raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")
                    elif not self.env.user.company_id.is_main and rec.product_id.create_uid.company_id.is_main:
                        raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")
                    elif not self.env.user.company_id.is_main and not rec.product_id.create_uid.company_id.is_main and not self.env.user.has_group("bizzup_price_access_customization.group_bpac_change_docs"):
                        raise ValidationError(" שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך.")

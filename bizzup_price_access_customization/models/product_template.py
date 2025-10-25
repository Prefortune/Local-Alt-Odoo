# -*- coding: utf-8 -*-
from xlwt.ExcelFormulaLexer import false_pattern

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_group = fields.Boolean(
        string="Is Group",
        copy=False,
        compute="_compute_is_group"
    )
    not_main_company = fields.Boolean(
        string="Not Main Company"
    )

    non_main_company_user = fields.Boolean(
        string="Not Main Company User"
    )

    @api.depends("name")
    def _compute_is_group(self):
        """Compute the group-related status."""
        for rec in self:
            rec.is_group = False
            rec.non_main_company_user = False
            if not self.env.user.company_id.is_main:
                rec.non_main_company_user = True
            if not self.env.user.has_groups("bizzup_price_access_customization.group_bpac_admin"):
                rec.is_group = True

    @api.model
    def create(self,vals):
        """Allow creation of new products while assigning company-specific values."""
        # Set company ID and other defaults for non-main companies
        if not self.env.user.company_id.is_main:
            vals["company_id"] = self.env.user.company_id.id
            vals["company_ids"] = [(6, 0, [self.env.user.company_id.id])]
            vals["not_main_company"] = True
        # Create the record
        return super(ProductTemplate,self).create(vals)

    def write(self,vals):
        """
        Restrict edits to certain fields for non-main companies.
        Non-main companies can edit their own products only.
        """
        for rec in self:
            # Check if the user's company is not main
            if not self.env.user.company_id.is_main and not self._context.get("params"):
                # If the product belongs to a user whose company is main, raise an error
                user = self.env['res.users'].search([('id', '=', rec.create_uid.id)])
                if user.company_id.is_main:
                    raise ValidationError(
                        " שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך."
                    )
        # Allow the update
        return super(ProductTemplate,self).write(vals)

    def unlink(self):
        """Restrict delete operation for non-main company."""
        for record in self:
            if not self.env.user.company_id.is_main:
                raise ValidationError(
                    " שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך."
                )
        return super(ProductTemplate,self).unlink()

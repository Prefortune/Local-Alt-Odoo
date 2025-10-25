# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.addons.product.models.product_product import ProductProduct


class ProductProductExtend(ProductProduct):
    _inherit = "product.product"

    def write(self, vals):
        """
        Restrict edits to certain fields for non-main companies.
        Non-main companies can edit their own products only.
        """
        for rec in self:
            # Check if the user's company is not main
            if not self.env.user.company_id.is_main:
                # If the product belongs to a user whose company is main, raise an error
                user = self.env["res.users"].search(
                    [("id", "=", rec.create_uid.id)]
                )
                if user.company_id.is_main and self.env.context.get('restrict_access'):
                    raise ValidationError(
                        " שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך."
                    )
                if (
                    user.company_id.is_main
                    and not self.env.user.has_group(
                        "bizzup_inventory_customization.group_allow_inventory_adjustment"
                    )
                    and self._context.get("is_inventory_adjustment", False)
                ):
                    raise ValidationError(
                        " שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך."
                    )
                if (
                    user.company_id.is_main
                    and self._context.get("is_inventory_adjustment", False)
                ):
                    raise ValidationError(
                        " שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך."
                    )
        # Allow the update
        return super(ProductProduct, self).write(vals)

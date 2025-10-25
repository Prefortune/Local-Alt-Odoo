# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.addons.product.models.product_template import ProductTemplate


class ProductTemplateExtend(ProductTemplate):
    _inherit = "product.template"

    def write(self, vals):
        """
        Restrict edits to certain fields for non-main companies.
        Non-main companies can edit their own products only.
        """
        restricted_fields = [
            'list_price',
            'type',
            'service_tracking',
            'service_policy',
            'create_repair',
            'taxes_id',
            'standard_price',
            'supplier_taxes_id',
            'categ_id',
            'discount_product',
            'default_code',
            'company_ids'
            'optional_product_ids',
            'accessory_product_ids',
            'alternative_product_ids',
            'product_tag_ids',
            'is_published',
            'website_id',
            'website_sequence',
            'public_categ_ids',
            'allow_out_of_stock_order',
            'website_ribbon_id',
            'show_availability',
            'out_of_stock_message',
            'product_template_image_ids',
            'description_sale',
            'description_ecommerce',
            'website_description',
            'expense_policy',
        ]
        for rec in self:
            # Check if the user's company is not main
            if not self.env.user.company_id.is_main:
                user = self.env["res.users"].search(
                    [("id", "=", rec.create_uid.id)]
                )
                if user.company_id.is_main:
                    for field in restricted_fields:
                        if field in vals:
                            raise ValidationError(
                                " שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך111."
                            )
                if user.company_id.is_main and self.env.context.get('restrict_access'):
                    raise ValidationError(
                        " שלום, אין לך הרשאות לשנות מחיר יחידה. אם תרצה בכל זאת לשנות את המחיר, אנא פנה למנהל שלך22222."
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
        return super(ProductTemplate, self).write(vals)

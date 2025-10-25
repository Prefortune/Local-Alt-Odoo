# -*- coding: utf-8 -*-

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def get_created_user_of_product(self, product):
        # Fetch the product record by name
        created_user = self.env['product.product'].browse(product).create_uid
        if self.env.user.company_id.is_main and self.env.user.has_group(
                        "bizzup_price_access_customization.group_bpac_change_docs"
                        ):
            return True
        elif not self.env.user.company_id.is_main and self.env.user.has_group(
                        "bizzup_price_access_customization.group_bpac_change_docs"
                        ) and not created_user.company_id.is_main:
            return True
        return False

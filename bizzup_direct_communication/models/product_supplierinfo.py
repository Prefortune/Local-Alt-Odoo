# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api

class ProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    direct_communication = fields.Boolean(string="Direct Communication")
    company_id = fields.Many2one('res.company', string="Company", readonly=True, default=lambda self: self.env.company)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """
        Make direct_communication field readonly
        for users not in the main company.
        """
        res = super(ProductSupplierInfo, self).fields_get(allfields, attributes)
        user = self.env.user
        if not user.company_id.is_main:
            res['direct_communication']['readonly'] = True
        return res

# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields


class MarginParameterWizard(models.TransientModel):
    _name = 'margin.parameter.wizard'
    _description = 'Margin Parameter Wizard'

    order_id = fields.Many2one('sale.order', 'Sale Order')

    def confirm_margin_parameter(self):
        """
        Confirm the sale order by directly setting its state to 'sale'.
        Used after margin warning approval.
        """
        sale_order = self.env['sale.order'].browse(self.order_id.id)
        sale_order.write({'state': 'sale'})

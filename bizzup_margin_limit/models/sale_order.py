# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api, _, SUPERUSER_ID


class SaleOrder(models.Model):
    _inherit = "sale.order"

    parent_id = fields.Many2one(
        'hr.employee',
        'Manager',
        default=lambda self: self._get_user_manager(),
        domain="['|', ('company_id', '=', False), ('company_id', 'in', allowed_company_ids)]",
        copy=False,
        )

    manager_approval = fields.Boolean('Manager Approval', copy=False)
    email_sent_manager = fields.Boolean('Email Sent to Manager', copy=False)


    def action_confirm(self):
        """
        Overrides order confirmation to enforce profitability checks and manager approval logic.
        Displays warning/blocking wizards based on margin thresholds.
        """
        error_parameter = self.env.company.error_parameter * 100
        limit_parameter = self.env.company.limit_parameter * 100
        if self.env.lang == 'en_US':
            block_name = 'Profitability Block'
            warning_name = 'Profitability Warning'
        else:
            block_name = 'חסימת ריווחיות'
            warning_name = 'אזהרת ריווחיות'
        for order in self:
            user_employees = self.env['hr.employee'].with_user(
                SUPERUSER_ID).search([('user_id','=',self.env.user.id)])
            if order.parent_id in user_employees:
                if order.manager_approval and order.email_sent_manager:
                    return super(SaleOrder,self).action_confirm()
            if limit_parameter > 0.0 or error_parameter > 0.0:
                sale_margin_percentage = order.margin_percent
                margin_percentage = sale_margin_percentage * 100
                margin_percentage = round(margin_percentage,2)
                if margin_percentage < limit_parameter:
                    return {
                        'type': "ir.actions.act_window",
                        'name': block_name,
                        'res_model': 'profit.approve.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_order_id': self.id,
                        }
                    }
                elif margin_percentage < error_parameter:
                    order.manager_approval = False
                    order.email_sent_manager = False
                    return {
                        'type': "ir.actions.act_window",
                        'name': warning_name,
                        'res_model': 'margin.parameter.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_order_id': self.id,
                        }
                    }
                else:
                    return super(SaleOrder,self).action_confirm()
            else:
                return super(SaleOrder,self).action_confirm()

    @api.model
    def _get_user_manager(self):
        """
        Returns the current user's manager (or self employee if no manager is assigned).
        Filters employees by current user and current company.
        """
        user_id = self._context.get('uid')
        user = self.env['res.users'].sudo().browse(user_id)
        current_company = self.env.company
        employee = user.sudo().employee_ids.filtered(
            lambda e: e.user_id.id == user_id and e.company_id.id == current_company.id
        )
        if employee:
            emp = employee[0]
            return emp.parent_id or emp
        else:
            return False

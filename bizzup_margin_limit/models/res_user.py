# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, _

class ResUser(models.Model):
    _inherit = "res.users"

    def check_manager_of_user(self, cashier):
        """
        Check if the currently logged-in user has an assigned manager.

        This method is intended to be called from the Point of Sale (POS) system.
        It verifies whether the employee record linked to the current user has a parent (manager).

        Returns:
            bool: True if the user has a manager assigned, False otherwise.
        """
        employee = self.env['hr.employee'].browse(cashier)
        if employee:
            if employee.parent_id:
                return True
            else:
                return False

    def get_manager_pin(self, cashier):
        """
        Retrieve the PIN code of the currently logged-in user's manager.

        This method is intended to be called from the Point of Sale (POS) system.
        It fetches the PIN from the manager (parent employee) of the current user's employee record.

        Returns:
            str or bool: The manager's PIN if available, otherwise False.
        """
        employee = self.env['hr.employee'].browse(cashier)
        if employee:
            if employee.parent_id:
                if employee.parent_id.pin:
                    return employee.parent_id.pin
                else:
                    return False

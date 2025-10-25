# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app
from odoo import models, fields, api
from odoo.exceptions import UserError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    project_type = fields.Selection([
        ('import_case', 'Import Case'),
        ('other', 'Other')
    ], string="Project Type")

    @api.model
    def create(self, vals):
        project = super().create(vals)
        if project.project_type:
            tasks = self.env['project.task'].search([('project_id', '=', project.id)])
            tasks.write({'import_case_type': project.project_type})
        return project

    def write(self, vals):
        res = super().write(vals)
        if 'project_type' in vals:
            for project in self:
                project.task_ids.write({'import_case_type': project.project_type})
        return res

    @api.onchange('project_type')
    def _onchange_project_type(self):
        if not self.env.user.has_group('project.group_project_manager'):  # 'Settings' group
            raise UserError(
                _(
                    "You do not have permission to change the Project Type"
                    )
                )
        
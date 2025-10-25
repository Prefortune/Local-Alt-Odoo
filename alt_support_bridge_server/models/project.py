from ast import Raise
from signal import raise_signal
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class DiscussChannel(models.Model):
    _inherit = "discuss.channel"
    project_id = fields.Many2one("project.project", string="Linked Project")


class ProjectTaskCreateWizard(models.TransientModel):
    _name = 'project.task.create.wizard'
    _description = 'Wizard to create task for a project'

    project_id = fields.Many2one('project.project', string="Project", required=True)
    name = fields.Char(string="Task Name", required=True)
    user_id = fields.Many2one('res.users', string="Assigned to")
    date_deadline = fields.Date(string="Deadline")
    allocated_hours = fields.Float(string="allocated_hours")
    alt_subscription_id = fields.Many2one(
        "subscription.package",
        string="Subscription",
        ondelete="cascade"
    )
    customer_id = fields.Many2one('res.partner',related='alt_subscription_id.partner_id',string="For Customer")
    description = fields.Html(string="Description")
    

    def action_create_task(self):

        if not self.customer_id.email:
            raise ValidationError("Please Add Email For Subscription User")
        
        _logger.info("------ self.customer_id.email --------- %s",self.customer_id.email)
        sub_allocated_hours = sum(self.alt_subscription_id.product_line_ids.mapped('product_qty'))
        consumed_hours = sum(self.alt_subscription_id.task_ids.mapped('effective_hours'))
        remaining_hours = sub_allocated_hours - (consumed_hours + self.allocated_hours)
        if remaining_hours < 0:
            raise ValidationError(_(
                "You cannot allocate %.2f hours. "
                "Only %.2f hours are remaining in the subscription "
                "(Total Allocated: %.2f, Consumed: %.2f)."
            ) % (self.allocated_hours, sub_allocated_hours - consumed_hours,
                 sub_allocated_hours, consumed_hours))

        if self.customer_id:
            res_users_table = self.env['res.users'].sudo()
            res_users = res_users_table.search([('partner_id','=',self.customer_id.id)],limit=1)
            if not res_users.exists():
                user = res_users_table.create({
                    'name' : self.customer_id.name,
                    'email' : self.customer_id.email,
                    'login': self.customer_id.email,
                    'active': True,
                    'password' : 123,
                    'partner_id' : self.customer_id.id,
                    'groups_id' : [(6, 0, [self.env.ref('base.group_portal').id])]
                }) 

        stages = self.env['project.task.type'].search([('project_ids', '=', self.project_id.id)], limit=1)
        if not stages:
            # Create a default stage and link it to the project
            stage = self.env['project.task.type'].create({
                'name': 'New',
                'project_ids': [(6, 0, [self.project_id.id])],
                'sequence': 1,
            })
        else:
            stage = stages

        """Create task on project"""
        self.ensure_one()
        task = self.env['project.task'].create({
            'name': self.name,
            'project_id': self.project_id.id,
            'user_ids' : [(4, self.user_id.id)],
            'stage_id': stage.id,
            'allocated_hours' : self.allocated_hours,
            'partner_id' : self.customer_id.id,
            'alt_subscription_id' : self.alt_subscription_id.id,
            'date_deadline' : self.date_deadline,
            'description' : self.description
        })
        return task

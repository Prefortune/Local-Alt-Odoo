from email.policy import default

from pkg_resources import require
from odoo import api, fields, models, _
from datetime import date, timedelta
import calendar
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError

CLOSED_STATES = {
    '1_done': 'Done',
    '1_canceled': 'Cancelled',
}

class ChangeRequestTask(models.Model):
    _name = 'change.request.task'

    partner_id = fields.Many2one(
        'res.partner',
        string="Created By",
        default=lambda self: self.env.user.partner_id
    )
    time = fields.Float(
        string="Allocated Time (Hours)",
    )
    note = fields.Char(
        string="Notes",
    )
    state = fields.Selection(
        [
            ('Pending', 'Pending'),
            ('Approved', 'Approved'),
            ('Cancelled', 'Cancelled'),
        ],
        string="Status",
        default='Pending',
        required=True
    )
    task_id = fields.Many2one(
        'project.task',
        string="Related Task",
    )

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.task_id:
            # When creating a Change Request → set task state to "Changes Requested"
            record.task_id.write({'state': '02_changes_requested'})
        return record


class ProjectTasks(models.Model):
    _inherit = "project.task"

    state = fields.Selection([
        ('00_new_state','New'),
        ('01_in_progress', 'In Progress'),
        ('02_changes_requested', 'Changes Requested'),
        ('03_approved', 'Approved'),
        *CLOSED_STATES.items(),
        ('04_waiting_normal', 'Waiting'),
        ('05_finished','Finished'),
    ], string='State', copy=False, default='00_new_state', required=True, compute='_compute_state', inverse='_inverse_state', readonly=False, store=True, index=True, recursive=True, tracking=True)


    alt_subscription_id = fields.Many2one(
        "subscription.package",
        string="Subscription",
        ondelete="cascade"
    )

    change_request_ids = fields.One2many('change.request.task','task_id')

    @api.depends('stage_id', 'depend_on_ids.state')
    def _compute_state(self):
        for task in self:
            dependent_open_tasks = []
            if task.allow_task_dependencies:
                dependent_open_tasks = [dependent_task for dependent_task in task.depend_on_ids if dependent_task.state not in CLOSED_STATES]
            # if one of the blocking task is in a blocking state
            if dependent_open_tasks:
                # here we check that the blocked task is not already in a closed state (if the task is already done we don't put it in waiting state)
                if task.state not in CLOSED_STATES:
                    task.state = '04_waiting_normal'
            # if the task as no blocking dependencies and is in waiting_normal, the task goes back to in progress

            # we comment below lines on Oct/2/25 bcz we don't want to change state 01_in_progress automatic
            # elif task.state not in CLOSED_STATES:
            #     task.state = '01_in_progress'


class SubscriptionPackage(models.Model):
    _inherit = "subscription.package"

    task_ids = fields.One2many(
        "project.task",
        "alt_subscription_id",
        string="Tasks"
    )
    
    discuss_channel_id = fields.Many2one('discuss.channel',string="Select Discuss Channel")

    def check_tasks(self):
        today = date.today()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1]) 
        _logger.info("--- today , first_day , last_day --- %s , %s , %s",today,first_day,last_day)

        subscription_package = self.env['subscription.package'].sudo().search([
            ('start_date','>=',first_day),
            ('next_invoice_date', '=', today),
            ('stage_id.category','=','progress'),
            ('task_ids', '!=', False)
        ])
        _logger.info("--- subscription_package --- %s",subscription_package)
        if not subscription_package:
            pass

        for subscription in subscription_package:
            incomplete_tasks = subscription.task_ids.filtered(lambda t: t.state not in ['1_done', '1_canceled'])
            next_month_first = (last_day + timedelta(days=1)).replace(day=1)
            next_month_last = (next_month_first.replace(day=calendar.monthrange(next_month_first.year, next_month_first.month)[1]))
            _logger.info("--- subscription , next_month_first --- next_month_last --- %s, %s , %s",incomplete_tasks , next_month_first , next_month_last)
            # Prepare task values for duplication
            task_vals = [
                (0, 0, {
                    'project_id' : task.project_id.id,
                    'name': task.name,
                    'description': task.description,
                    'user_ids': [(6,0,task.user_ids.ids)],
                    'allocated_hours': task.allocated_hours,
                })
                for task in incomplete_tasks
            ]
            newsubscription = subscription.create({
                'reference_code' : self.env['ir.sequence'].next_by_code('sequence.reference.code') or 'New',
                'partner_id' : subscription.partner_id.id,
                'plan_id' : subscription.plan_id.id,
                'start_date' : next_month_first,
                'next_invoice_date' : next_month_last,
                'product_line_ids' : [(0, 0,{
                    'product_id' : firstline.product_id.id,
                    'product_qty' : firstline.product_qty,
                }) for firstline in subscription.product_line_ids[0]],
                'task_ids' : task_vals,
                'discuss_channel_id' : subscription.discuss_channel_id.id
            })
            newsubscription.message_post(body=f"Subscription created automatically via Cron Job. Based on Subscription {subscription.name}")
            _logger.info("--- newsubscription --- %s",newsubscription)

    @api.constrains('partner_id','start_date','next_invoice_date')
    def subscription_package(self):
        for res in self:
            _logger.info("--- res.partner_id %s res.start_date %s res.next_invoice_date %s ---",res.partner_id , res.start_date , res.next_invoice_date)
            if not res.partner_id or not res.start_date or not res.next_invoice_date:
                continue

            # if res.start_date >= res.next_invoice_date:
            #     raise ValidationError(_(
            #             "The subscription start date must be earlier than the next invoice date. "
            #     ))

            today = date.today()
            subscriptions = res.env['subscription.package'].search([
                ('discuss_channel_id','=',res.discuss_channel_id.id),
                ('start_date','>=',res.start_date),
                ('next_invoice_date', '<=', res.next_invoice_date),
                ('id', '!=', res.id),
                ('stage_id.category','=','progress')
            ],limit=1)
            if subscriptions:
                raise ValidationError(_(
                        "This customer already has a subscription for this month. "
                        "Only one subscription per customer is allowed per month."
                ))


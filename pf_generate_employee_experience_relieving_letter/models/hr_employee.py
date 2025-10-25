from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    joining_date = fields.Date(string="Joining Date",  default=lambda self: date.today() - timedelta(days=1) )
    leaving_date = fields.Date(string="Leaving Date",  default=lambda self: date.today() + timedelta(days=1))

    def action_generate_experience_certificate(self):
        self.ensure_one()
        if self.joining_date and self.leaving_date and self.leaving_date <= self.joining_date:
                raise ValidationError("Leaving Date must be greater than Joining Date.")
        return self.env.ref('pf_generate_employee_experience_relieving_letter.action_report_experience_certificate').report_action(self)

    def action_generate_relieving_certificate(self):
        self.ensure_one()
        if self.joining_date and self.leaving_date and self.leaving_date <= self.joining_date:
                raise ValidationError("Leaving Date must be greater than Joining Date.")
        return self.env.ref('pf_generate_employee_experience_relieving_letter.action_report_relieving_certificate').report_action(self)

    def action_report_experience_certificate(self):
        return self.action_generate_experience_certificate()

    def action_report_relieving_certificate(self):
        return self.action_generate_relieving_certificate()

    @api.model
    def action_from_context(self):
        method = self.env.context.get('default_call_method')
        if method and hasattr(self, method):
            return getattr(self, method)()
        raise ValidationError("No valid method specified in context.")
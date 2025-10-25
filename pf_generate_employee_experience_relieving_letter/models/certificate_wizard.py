from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class CertificateWizard(models.TransientModel):
    _name = 'certificate.wizard'
    _description = 'Certificate Generation Wizard'

    certificate_type = fields.Selection([
        ('experience', 'Experience Certificate'),
        ('relieving', 'Relieving Certificate'),
    ], string='Certificate Type', required=True)
    certificate_issue_date = fields.Date(string='Certificate Issue Date', required=True, default=fields.Date.today, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    joining_date = fields.Date(string='Joining Date', required=True)
    ending_date = fields.Date(string='Ending Date', required=True)

    @api.model
    def default_get(self, fields):
        res = super(CertificateWizard, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if active_id:
            employee = self.env['hr.employee'].sudo().browse(active_id)
            if not employee.exists():
                _logger.error("No employee found for active_id: %s", active_id)
                raise ValidationError("Employee not found.")
            res.update({
                'employee_id': employee.id,
                'job_id': employee.job_id.id,
                'joining_date': employee.joining_date,
                'ending_date': employee.leaving_date,
            })
        certificate_type = self.env.context.get('certificate_type')
        if certificate_type:
            res['certificate_type'] = certificate_type
        _logger.info("Wizard default_get: %s", res)
        return res

    def action_generate_certificate(self):
        self.ensure_one()
        if not self.joining_date or not self.ending_date:
            raise ValidationError("Joining and Ending Dates are required.")
        if self.joining_date and self.ending_date and self.ending_date <= self.joining_date:
            raise ValidationError("Leaving Date must be greater than Joining Date.")
        if not self.employee_id.exists():
            _logger.error("Employee record does not exist: %s", self.employee_id.id)
            raise ValidationError("Employee record not found.")
        
        # Prepare context with wizard data in d-m-y format
        context = {
            'certificate_issue_date': self.certificate_issue_date.strftime('%d-%m-%y'),
            'wizard_joining_date': self.joining_date.strftime('%d-%m-%y'),
            'wizard_ending_date': self.ending_date.strftime('%d-%m-%y'),
        }
        _logger.info("Calling hr.employee function for %s certificate for employee %s (ID: %s) with context: %s",
                     self.certificate_type, self.employee_id.name, self.employee_id.id, context)
        
        # Call the appropriate hr.employee function
        employee = self.env['hr.employee'].sudo().browse(self.employee_id.id)
        if self.certificate_type == 'experience':
            return employee.with_context(**context).action_generate_experience_certificate()
        else:
            return employee.with_context(**context).action_generate_relieving_certificate()
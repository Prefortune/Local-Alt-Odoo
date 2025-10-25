from odoo import models, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        if 'phone' in vals:
            vals['phone'] = self.env['res.partner']._clean_phone_static(vals['phone'])
        if 'mobile' in vals:
            vals['mobile'] = self.env['res.partner']._clean_phone_static(vals['mobile'])
        return super().create(vals)

    def write(self, vals):
        if 'phone' in vals:
            vals['phone'] = self.env['res.partner']._clean_phone_static(vals['phone'])
        if 'mobile' in vals:
            vals['mobile'] = self.env['res.partner']._clean_phone_static(vals['mobile'])
        return super().write(vals)

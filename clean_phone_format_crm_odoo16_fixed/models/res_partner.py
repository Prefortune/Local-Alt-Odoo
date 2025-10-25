from odoo import models, api
import re

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if 'phone' in vals:
            vals['phone'] = self._clean_phone_static(vals['phone'])
        if 'mobile' in vals:
            vals['mobile'] = self._clean_phone_static(vals['mobile'])
        return super().create(vals)

    def write(self, vals):
        if 'phone' in vals:
            vals['phone'] = self._clean_phone_static(vals['phone'])
        if 'mobile' in vals:
            vals['mobile'] = self._clean_phone_static(vals['mobile'])
        return super().write(vals)

    @staticmethod
    def _clean_phone_static(phone):
        if not phone:
            return ''
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('972') and len(digits) >= 11:
            digits = '0' + digits[3:]
        elif len(digits) == 9 and digits.startswith('5'):
            digits = '0' + digits
        return digits

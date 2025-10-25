from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals):
        vals = self._add_country_code(vals)
        vals = self._phone_to_mobile(vals)
        return super().create(vals)

    
    def _phone_to_mobile(self, vals):
        """
        If mobile is not explicitly set in vals, copy phone into it.
        """
        if 'phone' in vals and vals['phone']:
            if not vals.get('mobile'):  # only set if mobile is missing/empty
                vals['mobile'] = vals['phone']
        return vals

    def _add_country_code(self, vals):
        """
        Automatically prepend the country code to the phone field if not present.
        """
        # Only run if phone is provided
        if 'phone' in vals and vals['phone']:
            country_code = None

            if 'country_id' in vals and vals['country_id']:
                country = self.env['res.country'].browse(vals['country_id'])
                country_code = country.phone_code

            elif self.country_id:
                country_code = self.country_id.phone_code

            elif not self.country_id:
                country_code = self.env['res.country'].search([('code','=','IL')]).phone_code

            if country_code:
                phone = vals['phone'].strip()
                # Add '+' if not already present
                if not phone.startswith(f'+{country_code}'):
                    # Remove leading 0 from local number if needed
                    if phone.startswith('0'):
                        phone = phone[1:]
                    vals['phone'] = f'+{country_code}{phone}'
        return vals

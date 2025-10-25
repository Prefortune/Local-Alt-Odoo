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
        _logger.info("--- _phone_to_mobile --- called %s",vals)

        if 'phone' in vals and vals['phone']:
            if not vals.get('mobile'):  # only set if mobile is missing/empty
                vals['mobile'] = vals['phone']
        return vals

    def _add_country_code(self, vals):
        """
        Automatically prepend the country code to the phone field if not present.
        """
        _logger.info("--- _add_country_code --- called %s",vals)

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

            _logger.info("_add_country_code function country_code is --> %s",country_code)
            if country_code:
                phone = vals['phone'].strip()
                # Add '+' if not already present
                if not phone.startswith(f'+{country_code}'):
                    # Remove leading 0 from local number if needed
                    if phone.startswith('0'):
                        phone = phone[1:]
                    vals['phone'] = f'+{country_code}{phone}'
        return vals


######### comment this all code Sep/22/2025 ######### and add above code 

# from odoo import models, api
# import re

# class ResPartner(models.Model):
#     _inherit = "res.partner"

#     @api.model_create_multi
#     def create(self, vals_list):
#         for vals in vals_list:
#             if vals.get("phone"):
#                 vals["phone"] = self._normalize_phone(vals["phone"], vals.get("country_id"))
#         return super().create(vals_list)

#     def write(self, vals):
#         if vals.get("phone"):
#             vals["phone"] = self._normalize_phone(vals["phone"], vals.get("country_id"))
#         return super().write(vals)

#     def _normalize_phone(self, phone, country_id):
#         phone = str(phone).strip()

#         # Remove any '+' not at the start
#         if '+' in phone[1:]:
#             phone = phone[0] + phone[1:].replace('+', '')

#         # Remove trailing '+'
#         phone = phone.rstrip('+')

#         # Get country code
#         country_code = ''
#         if country_id:
#             country = self.env['res.country'].browse(country_id)
#             country_code = str(country.phone_code) if country.phone_code else ''

#         # Prepend country code if missing and phone is local digits
#         if country_code and not phone.startswith('+'):
#             phone = f'+{country_code}{phone}'

#         # Keep +<country_code> format as-is if correct
#         return phone

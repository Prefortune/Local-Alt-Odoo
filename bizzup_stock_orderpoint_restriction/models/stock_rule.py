from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare



class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)

        is_po_consig = False
        if values.get('orderpoint_id'):
            is_po_consig = values['orderpoint_id'].location_id.consignation_locations or False

        domain += (('is_po_consig', '=', is_po_consig),)
        print("\n\n\ndomain", domain)

        return domain

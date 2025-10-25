from odoo import api,models, fields
import html
import re

class ResCompany(models.Model):
    _inherit = 'res.company'

    pf_signature = fields.Binary("Company Signature", attachment=True, help="Upload company signature for reports.")

    def clean_report_header(self):
        header = self.report_header or ''
        # Remove trailing <br>, empty <p></p>, or whitespace
        header = re.sub(r'(\s*(<br\s*/?>|\<p\>\s*\</p\>)\s*)+$', '', header, flags=re.IGNORECASE)
        return header.strip()

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pf_confimation_number = fields.Char(string="Confirmation Number")

    pf_title = fields.Char(string="Title")

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals['pf_title'] = self.pf_title
        return invoice_vals

class AccountMove(models.Model):
    _inherit = 'account.move'

    pf_title = fields.Char(string="Title")

class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    pf_signature_layout = fields.Binary(related='company_id.pf_signature', readonly=False)


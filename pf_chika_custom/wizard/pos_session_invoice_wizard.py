from odoo import models, fields, api
from odoo.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError

class PosSessionInvoiceWizard(models.TransientModel):
    _name = 'pos.session.invoice.wizard'
    _description = 'POS Session Invoice Wizard'

    session_id = fields.Many2one('pos.session', required=True)
    partner_id = fields.Many2one('res.partner', string='Agent', required=True)
    agent_commission = fields.Float(string='Agent Commission', default=0.0)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',required=True)

    def action_create_invoice(self):
        self.ensure_one()
        session = self.session_id
        partner = self.partner_id

        product_data = {}
        tax_decimal_sum = 0.0
        for order in session.order_ids:
            for line in order.lines:
                taxes = line.tax_ids_after_fiscal_position.compute_all(
                    line.price_unit,
                    line.order_id.pricelist_id.currency_id,
                    line.qty,
                    product=line.product_id,
                    partner=line.order_id.partner_id,
                )
                tax_amount = taxes['total_included'] - taxes['total_excluded']
                _logger.info("Computed tax amount for line %s: %s", line.id, tax_amount)
                decimal_part = tax_amount - int(tax_amount)
                tax_decimal_sum += decimal_part
                _logger.info("tax_decimal_sum: %s", tax_decimal_sum)

                key = (line.product_id.id, line.price_unit, line.discount, tuple(line.tax_ids_after_fiscal_position.ids))
                if key not in product_data:
                    product_data[key] = {
                        'product_id': line.product_id.id,
                        'quantity': 0,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'tax_ids': [(6, 0, line.tax_ids_after_fiscal_position.ids)],
                        'name': line.product_id.display_name,
                    }
                product_data[key]['quantity'] += line.qty

        if not product_data:
            raise ValidationError('No products found in POS session orders to invoice.')

        invoice_lines = []
        for data in product_data.values():
            invoice_lines.append((0, 0, {
                'product_id': data['product_id'],
                'quantity': data['quantity'],
                'price_unit': data['price_unit'],
                'discount': data['discount'],
                'tax_ids': data['tax_ids'],
                'name': data['name'],
            }))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_line_ids': invoice_lines,
            'pos_session_id': session.id,
        })
        session.invoice_id = invoice.id

        if abs(tax_decimal_sum) > 0.0001:
            # Add a rounding line
            invoice.line_ids = [(0, 0, {
                'name': 'Rounding Adjustment',
                'quantity': 1,
                'price_unit': tax_decimal_sum,
                'account_id': invoice.line_ids[0].account_id.id if invoice.line_ids else False,
            })] + [(1, line.id, {}) for line in invoice.line_ids]

        # Add agent commission as a line if set (after rounding adjustment)
        if self.agent_commission:
            analytic_distribution = {}
            if self.analytic_account_id:
                analytic_distribution = {str(self.analytic_account_id.id): 100.0}
            invoice.line_ids = [(0, 0, {
                'name': 'Agent Commission',
                'quantity': 1,
                'price_unit': -abs(self.agent_commission),
                'analytic_distribution': analytic_distribution,
                # Optionally set an account or product_id if needed
            })] + [(1, line.id, {}) for line in invoice.line_ids]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

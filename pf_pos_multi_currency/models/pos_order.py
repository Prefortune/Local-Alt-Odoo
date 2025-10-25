from odoo import api, fields, models, tools, _
from odoo.osv.expression import AND
from odoo.tools import float_is_zero, float_round, float_repr, float_compare
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_is_zero, float_round, float_repr
from functools import partial

class PosPayment(models.Model):
    """Adding currency symbol and amount."""
    _inherit = 'pos.payment'

    payment_currency = fields.Char(string='Payment Currency',
                                   help='Currency in POS settings.')
    currency_amount = fields.Float(string='Currency Amount',
                                   help='Currency amount settings.')
       
    
class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    pf_line_note = fields.Char('Line Note')

    def _export_for_ui(self, orderline):
        result = super()._export_for_ui(orderline)
        result['pf_line_note'] = orderline.pf_line_note
        return result

class PosOrder(models.Model):
    _inherit = "pos.order"

    custom_currency_id = fields.Many2one('res.currency','custom_currency_id')
    is_partial_payment = fields.Boolean(string="Is Partial Payment",
                                        default=False,
                                        help="Flag indicating whether this POS "
                                             "order is a partial payment.")
    due_amount = fields.Float(string="Amount Due",
                              compute='_compute_due_amount',
                              store=True,
                              help="The amount remaining to be paid for this"
                                   "POS order.")
    

    
   
    
    @api.model
    def _payment_fields(self, order, ui_paymentline):
        """Prepare and return a dictionary containing payment fields from the
         user interface payment line.
        params:
        order (pos.order): The POS order to which the payment belongs.
        ui_paymentline (dict): Payment information from the user interface."""
        # print("\n\n\n..............ui_paymentline['amount']...............",ui_paymentline['amount'],order.currency_id,order.custom_currency_id.id)
        vals= {
            'amount': ui_paymentline['amount'] or 0.0,
            'payment_date': ui_paymentline['name'],
            'payment_method_id': ui_paymentline['payment_method_id'],
            'card_type': ui_paymentline.get('card_type'),
            'cardholder_name': ui_paymentline.get('cardholder_name'),
            'transaction_id': ui_paymentline.get('transaction_id'),
            'payment_status': ui_paymentline.get('payment_status'),
            'ticket': ui_paymentline.get('ticket'),
            'pos_order_id': order.id,
            'payment_currency': ui_paymentline.get('payment_currency'),
            'currency_amount': ui_paymentline.get('currency_amount')
        }
        # print("\n\n\n.............................custom_currency_id",order.custom_currency_id,self.custom_currency_id,ui_paymentline.get('currency_amount'),ui_paymentline.get('payment_currency'))
        if order.custom_currency_id != order.currency_id:
            rate = order.custom_currency_id._get_conversion_rate(order.custom_currency_id, order.currency_id, order.company_id, order.date_order)
            # print("\n\n\n..............rate.............",float_repr(rate * vals['amount'],order.currency_id.decimal_places))
            vals.update({                
                'amount':float_repr(rate * vals['amount'],order.currency_id.decimal_places)
            })
            # print("\n\n\n..............................vals....",vals)
        return vals
    

    @api.depends('amount_total', 'amount_paid')
    def _compute_due_amount(self):
        """
        Compute the due amount for the POS order.

        This method computes the difference between the total amount and the amount paid
        for the POS order and updates the 'due_amount' field accordingly.
        """
        for record in self:
            # print("\n\n\n...........record.amount_paid.........",record.amount_paid,record.amount_total)
            record.due_amount = record.amount_total - record.amount_paid

    def _order_fields(self, ui_order):
        """
        Prepare dictionary for create method

        This method prepares a dictionary of order fields for creating a POS order based
        on the data from the user interface (UI) order.
        """
        # print("\n\n\\n........ui_order.get('custom_currency_id')....",self,ui_order.get('custom_currency_id'))
        result = super()._order_fields(ui_order)
        result['is_partial_payment'] = ui_order.get('is_partial_payment')
        result['custom_currency_id'] = ui_order.get('custom_currency_id')
        # if result['custom_currency_id'] != self.company_id.currency_id.id:            
        #     result.update({                
        #         'amount_paid':float_repr(0.01 * result['amount_paid'],self.company_id.currency_id.decimal_places)
        #     })
        #     print("\n\n\n..............................vals....",result)
        # result['currency_id']= ui_order.get('custom_currency_id')
        return result
    
    def add_payment(self, data):
        """Create a new payment for the order"""
        self.ensure_one()
        obj =self.env['pos.payment'].create(data)
        # print("\n\n\n................obj....",obj)
        self.amount_paid = sum(self.payment_ids.mapped('amount'))

    def action_pos_order_paid(self):
        """
        Mark the POS order as paid. This method marks the POS order as
        paid and ensures that it is fully paid based on the partial
        payment.
        """
        self.ensure_one()
        # TODO: add support for mix of cash and non-cash payments when both cash_rounding and only_round_cash_method are True
        if not self.config_id.cash_rounding \
                or self.config_id.only_round_cash_method \
                and not any(
            p.payment_method_id.is_cash_count for p in self.payment_ids):
            total = self.amount_total
        else:
            total = float_round(self.amount_total,
                                precision_rounding=self.config_id.rounding_method.rounding,
                                rounding_method=self.config_id.rounding_method.rounding_method)
        isPaid = float_is_zero(total - self.amount_paid,
                               precision_rounding=self.custom_currency_id.rounding)
        if not isPaid:
            pos_config = self.env['pos.config'].search([])
            for shop in pos_config:
                # print("\n\\nn........................shop....",shop)
                if shop.partial_payment:
                    isPaid = True
        if not isPaid and not self.config_id.cash_rounding:
            raise UserError(_("Order %s is not fully paid.", self.name))
        elif not isPaid and self.config_id.cash_rounding:
            currency = self.custom_currency_id
            if self.config_id.rounding_method.rounding_method == "HALF-UP":
                maxDiff = currency.round(
                    self.config_id.rounding_method.rounding / 2)
            else:
                maxDiff = currency.round(
                    self.config_id.rounding_method.rounding)

            diff = currency.round(self.amount_total - self.amount_paid)
            if not abs(diff) <= maxDiff:
                raise UserError(_("Order %s is not fully paid.", self.name))
        self.write({'state': 'paid'})
        return True

    @api.model
    def search_partial_order_ids(self, config_id, domain, limit, offset):
        """Search for 'partial' orders that satisfy the given domain,
        limit and offset."""
        default_domain = ['&', ('config_id', '=', config_id),
                          ('is_partial_payment', '=', True), '!', '|',
                          ('state', '=', 'draft'), ('state', '=', 'cancelled')]
        real_domain = AND([domain, default_domain])
        ids = self.search(AND([domain, default_domain]), limit=limit,
                          offset=offset).ids
        totalCount = self.search_count(real_domain)
        return {'ids': ids, 'totalCount': totalCount}
    

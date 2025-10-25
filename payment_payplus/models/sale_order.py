import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
import json
class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    is_warning_div = fields.Boolean(string="Warning Div", compute="_compute_is_warning_div")

    # @api.depends('transaction_ids', 'invoice_ids.payment_state')
    def _compute_is_warning_div(self):
        for order in self:
            show_warning = False

            # Step 1: Get the PayPlus transaction
            transaction = order.transaction_ids and order.transaction_ids[0] or None
            if (
                transaction and
                transaction.provider_id.code == 'payplus' and
                transaction.payplus_payment_success_response_json
            ):
                try:
                    payplus_response = transaction.payplus_payment_success_response_json
                    json_response = (
                        json.loads(payplus_response)
                        if isinstance(payplus_response, str)
                        else payplus_response
                    )
                    payment_type = json_response.get('type')
                    _logger.info("PayPlus payment_type: %s", payment_type)

                    # Step 2: Check if payment_type is 'Approval'
                    if payment_type == 'Approval':
                        # Step 3: Then check invoice is unpaid
                        if order.invoice_ids:
                            payment_states = order.invoice_ids.mapped('payment_state')
                            if any(state not in ['paid', 'partial', 'reversed', 'in_payment'] for state in payment_states):
                                show_warning = True
                        else:
                            show_warning = True

                except Exception as e:
                    _logger.warning("Failed to parse PayPlus JSON response: %s", e)

            order.is_warning_div = show_warning

    # def _check_is_warning_div_or_not(self):
    #     for res in self:
    #         if res.transaction_ids:
    #             invoice_id = res.invoice_ids
    #             if invoice_id.payment_state in ['paid' , 'partial' , 'reversed' , 'in_payment']:
    #                 res.is_warning_div = False
    #             else:
    #                 res.is_warning_div = True

    #             transaction_id = res.transaction_ids[0] if res.transaction_ids else None
    #             if transaction_id and transaction_id.provider_id.code == 'payplus' and transaction_id.payplus_payment_success_response_json :
    #                 payplus_response = transaction_id.payplus_payment_success_response_json
    #                 json_response = json.loads(payplus_response) if isinstance(payplus_response, str) else payplus_response
    #                 payment_type = json_response.get('type')
    #                 _logger.info("payment_type is getting ------------ %s",payment_type)
    #                 if payment_type == 'Approval':
    #                     res.is_warning_div = True
    #                 else:
    #                     res.is_warning_div = False
    #             else:
    #                 res.is_warning_div = False
    #         else:
    #             res.is_warning_div = False

from odoo import http
from odoo.http import request

class PayPlusController(http.Controller):

    @http.route('/payment/payplus/redirect', type='http', auth='public', methods=['POST'], csrf=False)
    def payplus_redirect(self, **kwargs):
        """Redirect to payplus payment page with required parameters."""
        return request.redirect('/payment/payplus/redirect')

    @http.route('/payment/payplus/return', type='http', auth='public', csrf=False)
    def payplus_return(self, **kwargs):
        """Handle successful payments by updating order status."""
        order = request.env['sale.order'].sudo().search([('name', '=', kwargs.get('myOrder'))])
        if order:
            order.sudo().write({'state': 'sale'})
        return request.redirect('/payment/status')

    @http.route('/payment/payplus/cancel', type='http', auth='public', csrf=False)
    def payplus_cancel(self, **kwargs):
        """Handle canceled payments."""
        return request.redirect('/payment/status?status=cancelled')

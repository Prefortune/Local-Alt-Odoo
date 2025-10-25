from odoo import http
from odoo.http import request

class CardcomController(http.Controller):

    @http.route('/payment/cardcom/redirect', type='http', auth='public', methods=['POST'], csrf=False)
    def cardcom_redirect(self, **kwargs):
        """Redirect to Cardcom payment page with required parameters."""
        return request.redirect('/payment/cardcom/redirect')

    @http.route('/payment/cardcom/return', type='http', auth='public', csrf=False)
    def cardcom_return(self, **kwargs):
        """Handle successful payments by updating order status."""
        order = request.env['sale.order'].sudo().search([('name', '=', kwargs.get('myOrder'))])
        if order:
            order.sudo().write({'state': 'sale'})
        return request.redirect('/payment/status')

    @http.route('/payment/cardcom/cancel', type='http', auth='public', csrf=False)
    def cardcom_cancel(self, **kwargs):
        """Handle canceled payments."""
        return request.redirect('/payment/status?status=cancelled')

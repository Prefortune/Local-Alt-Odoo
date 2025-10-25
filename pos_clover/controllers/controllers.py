from odoo import http
from odoo.http import request
import logging
import json

_logger = logging.getLogger(__name__)

class CloverController(http.Controller):

    @http.route('/clover/webhook', type='http', auth='none', methods=['POST','GET'], csrf=False)
    def clover_webhook(self, **post):
        try:
            # Detect method and read data
            if request.httprequest.method == 'POST':
                data = json.loads(request.httprequest.data.decode()) if request.httprequest.data else {}
            else:  # GET request: use query params
                data = dict(request.params)

            # Log to Odoo log
            _logger.info("Clover Webhook received: %s", json.dumps(data))
            _logger.info("Query Params: %s", request.params)

            # Optional: Save webhook in database
            request.env['clover.webhook.log'].sudo().create({
                'payload': json.dumps(data),
                'params': json.dumps(request.params),
                'response': json.dumps({'status': 'success'}),
                'status': 'success',
            })

            # Process POS order
            order_id = data.get('order', {}).get('id') or data.get('order_id')
            payment_state = data.get('paymentState') or data.get('payment_state')

            if order_id and payment_state:
                pos_order = request.env['pos.order'].sudo().search([('name', '=', order_id)], limit=1)
                if pos_order and str(payment_state).upper() == 'PAID':
                    pos_order.sudo().write({'state': 'paid'})
                    _logger.info("POS Order %s marked as paid", order_id)

            # Return JSON response
            return request.make_response(
                json.dumps({'status': 'success'}),
                headers=[('Content-Type', 'application/json')]
            )
        except Exception as e:
            _logger.error("Error processing Clover webhook: %s", e)

            # Optional: Save error in webhook log
            request.env['clover.webhook.log'].sudo().create({
                'payload': json.dumps(request.httprequest.data.decode() if request.httprequest.data else {}),
                'params': json.dumps(request.params),
                'response': json.dumps({'status': 'error', 'message': str(e)}),
                'status': 'error',
            })

            return request.make_response(
                json.dumps({'status': 'error', 'message': str(e)}),
                headers=[('Content-Type', 'application/json')]
            )

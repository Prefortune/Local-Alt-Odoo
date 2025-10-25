# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import logging
import json

_logger = logging.getLogger(__name__)

class ShopifyHelpdesk(http.Controller):
    @http.route('/create/helpdesk_ticket', type='http', auth='public', methods=['POST'], csrf=False)
    def create_helpdesk_ticket(self, **kwargs):
        req = request.params
        _logger.info("req %s", req)

        name = req.get('name')
        email = req.get('email')
        body = req.get('body')

        if not name or not email or not body:
            helpdesk_data = {
                'success': False,
                'message': 'Name, email, and body are required'
            }
            return Response(
                json.dumps(helpdesk_data),
                content_type='application/json',
                headers={'Access-Control-Allow-Origin': '*'}
            )

        # Fetch configuration values
        config_params = request.env['ir.config_parameter'].sudo()
        helpdesk_id = config_params.get_param('helpdesk.default_team_id')
        ticket_type_id = config_params.get_param('helpdesk.default_ticket_type_id')
        tag_id = config_params.get_param('helpdesk.default_tag_id')

        # Create the helpdesk ticket
        ticket = request.env['helpdesk.ticket'].sudo().create({
            'name': name,
            'description': body,
            'email_cc': email,
            'team_id': int(helpdesk_id) if helpdesk_id else False,
            'ticket_type_id': int(ticket_type_id) if ticket_type_id else False,
            'tag_ids': [(6, 0, [int(tag_id)])] if tag_id else False,
        })

        helpdesk_data = {
            'success': True,
            'message': 'Helpdesk ticket created successfully',
            'ticket_id': ticket.id,
        }

        return Response(
            json.dumps(helpdesk_data),
            content_type='application/json',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )

    # Handle CORS preflight request
    @http.route('/create/helpdesk_ticket', type='http', auth='public', methods=['OPTIONS'], csrf=False)
    def preflight(self, **kwargs):
        return Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )
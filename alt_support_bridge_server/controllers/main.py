from encodings import charmap
import json
import logging
from math import fabs
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class AltSupportController(http.Controller):
    
    @http.route('/alt_support/message', type='json', auth='public', csrf=False)
    def receive_message(self, **kwargs):
        """Receive message from client and create/update channel."""
        try:
            data = json.loads(request.httprequest.data)
            company_name = data.get('company_name')
            user_name = data.get('user_name')
            message = data.get('message')
            
            if not all([company_name, user_name, message]):
                return {'error': 'Missing required fields'}
            
            # Find or create shared channel
            channel = request.env['discuss.channel'].sudo().search([
                ('name', '=', f'alt support - {company_name}')
            ], limit=1)
            
            if not channel:
                channel = request.env['discuss.channel'].sudo().create({
                    'name': f'alt support - {company_name}',
                    'channel_type': 'channel',
                    'description': f'Shared support channel for {company_name}'
                })
            
            # Post message
            channel.message_post(
                body=message,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=request.env.user.partner_id.id
            )
            
            return {'success': True, 'channel_id': channel.id}
            
        except Exception as e:
            return {'error': str(e)}

    @http.route('/alt-support/receive', type='json', auth='public', csrf=False)
    def receive_message_new(self, **kwargs):
        """Receive message from client and create/update channel."""
        try:
            data = json.loads(request.httprequest.data)
            _logger.info("--> /alt-support/receive data %s",data)
            company_name = data.get('company_name')
            author_name = data.get('author_name')
            message_body = data.get('body')
            channel_type = data.get('channel_type', 'shared')
            client_message_id = data.get('client_message_id')
            is_thread = data.get('is_thread',False)
            thread_name = data.get('thread_name',False)
            from_message_id = data.get('from_message_id',False)
            client_channel_id = data.get('client_channel_id',False)
            if is_thread:
                channel_type = 'personal'

            if not all([company_name, author_name, message_body]):
                return {'error': 'Missing required fields'}
            
            # Find or create channel based on type
            channel_name = f'alt support - {company_name}'
            if channel_type == 'personal':
                channel_name = f'{channel_name} - {author_name}'

            channel = request.env['discuss.channel'].sudo().search([
                ('name', '=', channel_name)
            ], limit=1)
            
            if not channel:
                channel = request.env['discuss.channel'].sudo().create({
                    'name': channel_name,
                    'channel_type': 'channel',
                    'description': f'Support channel for {company_name}'
                })
            
            # Find or create partner for the author
            author_partner = request.env['res.partner'].sudo().search([
                ('name', '=', author_name)
            ], limit=1)
            
            if not author_partner:
                author_partner = request.env['res.partner'].sudo().create({
                    'name': author_name,
                    'is_company': False
                })

            _logger.info("=== parent_channel_id : %s",channel.name)
            _logger.info("=== channel_name : %s",channel_name)
            if is_thread:
                _logger.info("=== thread_name : %s",thread_name)

                thread_channel = request.env['discuss.channel'].sudo().search([
                    ('name','=',thread_name),
                    ('parent_channel_id','=',channel.id)
                ],limit=1)
                if not thread_channel:

                    thread_channel = channel._create_sub_channel(from_message_id, thread_name)
                    thread_channel.write({
                        'client_channel_id' : client_channel_id,
                        'channel_member_ids': [
                            (0, 0, {'partner_id': partner.id})
                            for partner in channel.channel_partner_ids
                        ]
                    })
                    # thread_channel = request.env['discuss.channel'].sudo().create({
                    #     'name' : thread_name,
                    #     'parent_channel_id' : channel.id,
                    #     'channel_member_ids': [
                    #         (0, 0, {'partner_id': partner.id})
                    #         for partner in channel.channel_partner_ids
                    #     ]
                    # })
                _logger.info("=== thread_name channel name : %s",channel)
                channel = thread_channel
            
            # Post message
            message = channel.with_context(is_from_client=True).message_post(
                body=message_body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=author_partner.id,
                # author_id=request.env.user.partner_id.id
            )

            message.write({
                'client_message_id' : client_message_id
            })
            
            # Send acknowledgment back to client
            # self._send_ack_to_client(company_name, message)
            
            return {'success': True, 'channel_id': channel.id}
            
        except Exception as e:
            _logger.error(f'Error receiving message: {str(e)}')
            return {'error': str(e)}

    def _send_ack_to_client(self, company_name, message):
        """Send acknowledgment back to client."""
        try:
            _logger.info(f"=== ALT SUPPORT SERVER: Starting acknowledgment for company: {company_name} ===")
            
            # Find client configuration
            token_config = request.env['ir.config_parameter'].sudo().get_param('alt_support.valid_tokens')
            _logger.info(f"=== ALT SUPPORT SERVER: Raw token config: {token_config} ===")
            
            if not token_config:
                _logger.warning(f'No token configuration found for company: {company_name}')
                return

            try:
                token_config = eval(token_config)  # Convert string to dict
            except Exception as e:
                _logger.error(f'Failed to parse token configuration: {str(e)}')
                return

            if company_name not in token_config:
                _logger.warning(f'No configuration found for company: {company_name}')
                return

            # Get client details
            client_config = token_config[company_name]
            client_url = client_config.get('url')
            server_token = client_config.get('server_token')  # Use server token

            if not client_url or not server_token:
                _logger.error(f'Missing client URL or server token for company: {company_name}')
                return

            # Prepare acknowledgment data
            ack_data = {
                'company_name': company_name,
                'author_name': 'Support Team',
                'body': f'✅ הודעה התקבלה בהצלחה: {message.body[:100]}...',
                'channel_type': 'shared',
                'is_ack': True
            }

            # Send acknowledgment to client
            import requests
            _logger.info(f"=== ALT SUPPORT SERVER: Sending acknowledgment to {client_url}/alt-support/receive ===")
            _logger.info(f"=== ALT SUPPORT SERVER: Acknowledgment data: {ack_data} ===")
            _logger.info(f"=== ALT SUPPORT SERVER: Client URL: {client_url} ===")
            _logger.info(f"=== ALT SUPPORT SERVER: Server Token: {server_token[:10] if server_token else 'None'}... ===")
            
            response = requests.post(
                f'{client_url}/alt-support/receive',
                json=ack_data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {server_token}'
                },
                timeout=5
            )

            _logger.info(f"=== ALT SUPPORT SERVER: Response status: {response.status_code} ===")
            _logger.info(f"=== ALT SUPPORT SERVER: Response content: {response.text} ===")

            if response.status_code == 200:
                _logger.info(f'Acknowledgment sent successfully to {company_name}')
            else:
                _logger.error(f'Failed to send acknowledgment to {company_name}: {response.text}')

        except Exception as e:
            _logger.error(f'Error sending acknowledgment to client: {str(e)}')

    @http.route('/alt-support/health', type='http', auth='none', csrf=False)
    def health_check(self, **kwargs):
        """Simple health check endpoint."""
        return json.dumps({'status': 'ok'}) 
import json
import logging
import re
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class AltSupportController(http.Controller):
    @http.route('/alt-support/receive', type='json', auth='public', csrf=False)
    def receive_message(self, **kwargs):
        """Receive message from server and create/update channel."""
        try:
            _logger.info(f"=== ALT SUPPORT CLIENT: Received message from server: {kwargs} ===")
            
            # Verify authorization header
            auth_header = request.httprequest.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                _logger.error("=== ALT SUPPORT CLIENT: Missing or invalid Authorization header ===")
                return {'error': 'Unauthorized'}
            
            # Extract and verify token
            token = auth_header.split('Bearer ')[1]
            expected_token = request.env['ir.config_parameter'].sudo().get_param('alt_support.server_token')
            _logger.info(f"=== ALT SUPPORT CLIENT: Received token: {token[:10] if token else 'None'}... ===")
            _logger.info(f"=== ALT SUPPORT CLIENT: Expected token: {expected_token[:10] if expected_token else 'None'}... ===")
            if not expected_token or token != expected_token:
                _logger.error("=== ALT SUPPORT CLIENT: Invalid token ===")
                _logger.error(f"=== ALT SUPPORT CLIENT: Token mismatch - received: {token}, expected: {expected_token} ===")
                return {'error': 'Invalid token'}
            
            # Get data from kwargs (Odoo automatically parses JSON body to kwargs)
            company_name = kwargs.get('company_name')
            author_name = kwargs.get('author_name')
            message_body = kwargs.get('body')
            channel_type = kwargs.get('channel_type', 'shared')
            is_ack = kwargs.get('is_ack', False)  # Check if this is an acknowledgment
            
            _logger.info(f"=== ALT SUPPORT CLIENT: Parsed data - company: {company_name}, author: {author_name}, body: {message_body[:50] if message_body else 'None'}... ===")
            _logger.info(f"=== ALT SUPPORT CLIENT: Raw kwargs: {kwargs} ===")
            _logger.info(f"=== ALT SUPPORT CLIENT: All kwargs keys: {list(kwargs.keys())} ===")
            
            # Check if any required field is None or empty
            if not company_name or not author_name or not message_body:
                _logger.error(f"=== ALT SUPPORT CLIENT: Missing required fields - company: {company_name}, author: {author_name}, body: {message_body} ===")
                _logger.error(f"=== ALT SUPPORT CLIENT: All kwargs keys: {list(kwargs.keys())} ===")
                return {'error': 'Missing required fields'}
            
            # Convert HTML to plain text if needed
            def html_to_text(html_content):
                if not html_content:
                    return ""
                # Remove HTML tags
                text = re.sub(r'<[^>]+>', '', html_content)
                # Decode HTML entities
                text = text.replace('&nbsp;', ' ')
                text = text.replace('&amp;', '&')
                text = text.replace('&lt;', '<')
                text = text.replace('&gt;', '>')
                text = text.replace('&quot;', '"')
                text = text.replace('&#39;', "'")
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                return text
            
            # Convert message body to plain text
            clean_message_body = html_to_text(message_body)
            
            # Find or create channel based on type
            channel_name = f'alt support - {company_name}'
            if channel_type == 'personal':
                channel_name = f'{channel_name} - {author_name}'
                
            _logger.info(f"=== ALT SUPPORT CLIENT: Looking for channel: {channel_name} ===")
            
            # Check available models for channels
            _logger.info(f"=== ALT SUPPORT CLIENT: Available models: {list(request.env.keys())} ===")
            
            # Try different channel models
            channel_model = None
            if 'discuss.channel' in request.env:
                channel_model = request.env['discuss.channel'].sudo()
                _logger.info(f"=== ALT SUPPORT CLIENT: Using discuss.channel model ===")
            elif 'mail.channel' in request.env:
                channel_model = request.env['mail.channel'].sudo()
                _logger.info(f"=== ALT SUPPORT CLIENT: Using mail.channel model ===")
            else:
                _logger.error(f"=== ALT SUPPORT CLIENT: No channel model found ===")
                return {'error': 'No channel model available'}
            
            _logger.info(f"=== ALT SUPPORT CLIENT: Channel model found: {channel_model} ===")
            
            channel = channel_model.search([
                ('name', '=', channel_name)
            ], limit=1)
            
            _logger.info(f"=== ALT SUPPORT CLIENT: Search result - found {len(channel)} channels ===")
            
            if not channel:
                _logger.info(f"=== ALT SUPPORT CLIENT: Creating new channel: {channel_name} ===")
                try:
                    channel = channel_model.create({
                        'name': channel_name,
                        'channel_type': 'channel',
                        'description': f'Support channel for {company_name}'
                    })
                    _logger.info(f"=== ALT SUPPORT CLIENT: Successfully created new channel: {channel.name} (ID: {channel.id}) ===")
                except Exception as e:
                    _logger.error(f"=== ALT SUPPORT CLIENT: Error creating channel: {str(e)} ===")
                    return {'error': f'Failed to create channel: {str(e)}'}
            else:
                _logger.info(f"=== ALT SUPPORT CLIENT: Found existing channel: {channel.name} (ID: {channel.id}) ===")
            
            # Find or create partner for the author
            _logger.info(f"=== ALT SUPPORT CLIENT: Looking for partner: {author_name} ===")
            author_partner = request.env['res.partner'].sudo().search([
                ('name', '=', author_name)
            ], limit=1)
            
            if not author_partner:
                _logger.info(f"=== ALT SUPPORT CLIENT: Creating new partner: {author_name} ===")
                try:
                    author_partner = request.env['res.partner'].sudo().create({
                        'name': author_name,
                        'is_company': False
                    })
                    _logger.info(f"=== ALT SUPPORT CLIENT: Successfully created partner: {author_partner.name} (ID: {author_partner.id}) ===")
                except Exception as e:
                    _logger.error(f"=== ALT SUPPORT CLIENT: Error creating partner: {str(e)} ===")
                    return {'error': f'Failed to create partner: {str(e)}'}
            else:
                _logger.info(f"=== ALT SUPPORT CLIENT: Found existing partner: {author_partner.name} (ID: {author_partner.id}) ===")
            
            # Post message (but don't forward if it's an acknowledgment)
            _logger.info(f"=== ALT SUPPORT CLIENT: Posting message to channel {channel.name} ===")
            _logger.info(f"=== ALT SUPPORT CLIENT: Message body: {clean_message_body} ===")
            _logger.info(f"=== ALT SUPPORT CLIENT: Author partner: {author_partner.name} (ID: {author_partner.id}) ===")
            
            try:
                message = channel.message_post(
                    body=clean_message_body,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                    author_id=author_partner.id
                )
                
                _logger.info(f"=== ALT SUPPORT CLIENT: Message posted successfully with ID: {message.id} ===")
                _logger.info(f"=== ALT SUPPORT CLIENT: Message content: {message.body} ===")
                _logger.info(f"=== ALT SUPPORT CLIENT: Message author: {message.author_id.name} ===")
                
                # Mark message as from server to prevent forwarding
                if is_ack:
                    message.write({'is_from_server': True})
                    _logger.info(f"=== ALT SUPPORT CLIENT: Message marked as from server ===")
                
                _logger.info(f"=== ALT SUPPORT CLIENT: Successfully processed message ===")
                return {'success': True, 'channel_id': channel.id}
                
            except Exception as e:
                _logger.error(f"=== ALT SUPPORT CLIENT: Error posting message: {str(e)} ===")
                # Try alternative method
                try:
                    _logger.info(f"=== ALT SUPPORT CLIENT: Trying alternative message posting method ===")
                    message = request.env['mail.message'].sudo().create({
                        'model': channel_model._name,
                        'res_id': channel.id,
                        'body': clean_message_body,
                        'message_type': 'comment',
                        'subtype_id': request.env.ref('mail.mt_comment').id,
                        'author_id': author_partner.id
                    })
                    _logger.info(f"=== ALT SUPPORT CLIENT: Alternative method successful - Message ID: {message.id} ===")
                    return {'success': True, 'channel_id': channel.id}
                except Exception as e2:
                    _logger.error(f"=== ALT SUPPORT CLIENT: Alternative method also failed: {str(e2)} ===")
                    return {'error': f'Failed to post message: {str(e)}'}
            
        except Exception as e:
            _logger.error(f'=== ALT SUPPORT CLIENT: Error receiving message: {str(e)} ===')
            return {'error': str(e)}

    @http.route('/alt-support/health', type='http', auth='none', csrf=False)
    def health_check(self, **kwargs):
        """Simple health check endpoint."""
        return json.dumps({'status': 'ok'}) 
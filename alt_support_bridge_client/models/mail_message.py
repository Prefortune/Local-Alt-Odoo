import json
import requests
import re
from odoo import models, fields, api
from odoo.exceptions import UserError

class MailMessage(models.Model):
    _inherit = 'mail.message'
    
    is_from_server = fields.Boolean(
        string='From Server',
        default=False,
        help='Indicates if this message was received from the support server'
    )

    def _is_support_channel(self, channel):
        """Check if the channel is a support channel."""
        return channel.name.startswith('alt support -')

    def _get_channel_type(self, channel):
        """Determine if the channel is shared or personal."""
        if ' - ' in channel.name:
            parts = channel.name.split(' - ')
            if len(parts) == 3:  # Company - User format
                return 'personal'
        return 'shared'

    @api.model
    def create(self, vals):
        message = super(MailMessage, self).create(vals)
        
        # Check if message is in a support channel and not from server
        if message.model == 'discuss.channel' and message.res_id:
            channel = self.env['discuss.channel'].browse(message.res_id)
            if self._is_support_channel(channel) and not vals.get('is_from_server'):
                self._forward_message_to_server(message, channel)
        
        return message

    def _forward_message_to_server(self, message, channel):
        """Forward the message to the support server."""
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            _logger.info(f"=== ALT SUPPORT CLIENT: Starting to forward message {message.id} ===")
            
            # Get server configuration from alt.support.config model
            config = self.env['alt.support.config'].sudo().search([], limit=1)
            
            _logger.info(f"=== ALT SUPPORT CLIENT: Found config: {config} ===")
            
            if not config:
                raise UserError('Support server configuration is missing. Please configure the settings in Alt Support Configuration.')
            
            server_url = config.server_url
            api_token = config.api_token

            _logger.info(f"=== ALT SUPPORT CLIENT: Server URL: {server_url} ===")
            _logger.info(f"=== ALT SUPPORT CLIENT: API Token: {api_token[:10] if api_token else 'None'}... ===")

            if not server_url or not api_token:
                raise UserError('Support server configuration is missing. Please set both Server URL and API Token.')

            # Prepare message data
            # Get company from author or channel
            company = message.author_id.company_id or self.env.company
            author = message.author_id
            
            _logger.info(f"=== ALT SUPPORT CLIENT: Using company: {company.name} ===")

            # Convert HTML to plain text
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

            message_data = {
                'message_id': message.id,
                'company_name': company.name,
                'author_name': author.name,
                'channel_type': self._get_channel_type(channel),
                'body': html_to_text(message.body),
                'timestamp': message.date.isoformat(),
            }

            # Add signature to message body
            signature = f'[{author.name} | {channel.name}]'
            if not message.body.startswith(signature):
                message.body = f'{signature}\n{message.body}'
                message.write({'body': message.body})

            # Send to server
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_token}'
            }

            _logger.info(f"=== ALT SUPPORT CLIENT: Sending to {server_url}/alt-support/receive ===")
            _logger.info(f"=== ALT SUPPORT CLIENT: Message data: {message_data} ===")

            response = requests.post(
                f'{server_url}/alt-support/receive',
                json=message_data,
                headers=headers
            )

            _logger.info(f"=== ALT SUPPORT CLIENT: Response status: {response.status_code} ===")
            _logger.info(f"=== ALT SUPPORT CLIENT: Response content: {response.text} ===")

            if response.status_code != 200:
                raise UserError(f'Failed to forward message: {response.text}')

        except Exception as e:
            # Log error but don't prevent message creation
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f'Alt Support Bridge Error: {str(e)}')
            
            # Try to create ir.logging record
            try:
                self.env['ir.logging'].create({
                    'name': 'Alt Support Bridge',
                    'type': 'server',
                    'dbname': self.env.cr.dbname,
                    'level': 'ERROR',
                    'message': f'Error forwarding message: {str(e)}',
                    'path': 'alt_support_bridge_client',
                    'func': '_forward_message_to_server',
                    'line': 1,
                })
            except Exception as log_error:
                _logger.error(f'Failed to create ir.logging: {str(log_error)}') 
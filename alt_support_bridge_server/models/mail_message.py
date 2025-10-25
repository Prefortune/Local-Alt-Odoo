import json
import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

print("=== ALT SUPPORT: mail_message.py loaded ===")
_logger.info("=== ALT SUPPORT: mail_message.py loaded ===")

# class MailMessageReaction(models.Model):
#     _inherit = 'mail.message.reaction'

#     @api.model
#     def create(self,vals):
#         res = super(MailMessageReaction, self).create(vals)
#         _logger.info("=== mail.message.reaction === Create %s %s",vals,res)

#         message = res.message_id
#         partner_id = res.partner_id.name
#         reaction = res.content


#         channel = self.env['discuss.channel'].browse(message.res_id)
#         _logger.info(f"=== ALT SUPPORT: Channel name: {channel.name} === {channel.id}")

#         if channel.name.startswith('alt support -') and not self.env.context.get('is_from_client'):
#             token_config = self.env['ir.config_parameter'].sudo().get_param('alt_support.valid_tokens')
#             if not token_config:
#                 _logger.warning('=== ALT SUPPORT: No token configuration found ===')
#                 return
        
#             try:
#                 _logger.info("=== ALT SUPPORT TYPE OF token_config === %s",type(token_config))
#                 token_config = eval(token_config)  # Convert string to dict
#                 _logger.info(f"=== ALT SUPPORT: Parsed token config: {token_config} ===")
#             except Exception as e:
#                 _logger.error(f'=== ALT SUPPORT: Failed to parse token configuration: {str(e)} ===')
#                 return
            
#             channel_parts = channel.name.split(' - ')
#             _logger.info(f"=== ALT SUPPORT: Channel parts: {channel_parts} ===")
            
#             if len(channel_parts) < 2:
#                 _logger.warning(f'=== ALT SUPPORT: Invalid channel name format: {channel.name} ===')
#                 return

#             company_name = channel_parts[1]
#             _logger.info(f"=== ALT SUPPORT: Extracted company name: {company_name} ===")
            
#             if company_name not in token_config:
#                 _logger.warning(f'=== ALT SUPPORT: No configuration found for company: {company_name} ===')
#                 _logger.warning(f'=== ALT SUPPORT: Available companies: {list(token_config.keys())} ===')
#                 return

#             # Get client details
#             client_config = token_config[company_name]
#             _logger.info(f"=== ALT SUPPORT: Client config for {company_name}: {client_config} ===")
            
#             client_url = client_config.get('url')
#             server_token = client_config.get('server_token')  # Use server token instead of client token
            
#             _logger.info(f"=== ALT SUPPORT: Client URL: {client_url} ===")
#             _logger.info(f"=== ALT SUPPORT: Server Token: {server_token[:10] if server_token else 'None'}... ===")

#             # return

#             reaction_data = {
#                 'message_id': message,
#                 'content': partner_id,
#                 'partner_id': partner_id,
#                 'guest_id': False
#             }
                            
#             _logger.info(f"=== ALT SUPPORT: Prepared reaction_data: {reaction_data} ===")
#             # Build the full URL
#             full_url = f"{client_url}/alt-support/reaction/receive"
#             _logger.info(f"=== ALT SUPPORT: Sending to full URL: {full_url} ===")
#             try:
#                 _logger.info(f"=== ALT SUPPORT: Making POST request to: {full_url} ===")
#                 _logger.info(f"=== ALT SUPPORT: JSON data: {json.dumps(reaction_data, indent=2)} ===")
#                 response = requests.post(
#                     full_url,
#                     json=reaction_data,
#                     headers={
#                         'Authorization': f'Bearer {server_token}',
#                         'Content-Type': 'application/json'
#                     },
#                     timeout=5
#                 )
#                 _logger.info(f"=== ALT SUPPORT: Response status: {response.status_code} ===")
#                 _logger.info(f"=== ALT SUPPORT: Response content: {response.text} ===")
#                 response.raise_for_status()
#                 _logger.info(f"=== ALT SUPPORT: Message sent successfully to {company_name} ===")
#             except requests.exceptions.Timeout:
#                 _logger.error(f'=== ALT SUPPORT: Timeout while sending message to client {company_name} ===')
#                 raise UserError('Connection to client timed out. Please try again.')
#             except requests.exceptions.RequestException as e:
#                 _logger.error(f'=== ALT SUPPORT: Failed to send message to client {company_name}: {str(e)} ===')
#                 raise UserError(f'Failed to send message to client: {str(e)}')
#             except Exception as e:
#                 _logger.error(f'=== ALT SUPPORT: Unexpected error while sending message to client {company_name}: {str(e)} ===')
#                 raise UserError(f'An unexpected error occurred: {str(e)}') 
        
#         return res

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        """Override create to handle outgoing messages."""
        print("=== ALT SUPPORT DEBUG: MailMessage.create called ===")
        _logger.info("=== ALT SUPPORT: MailMessage.create called ===")
        
        message = super(MailMessage, self).create(vals)
        
        print(f"=== ALT SUPPORT DEBUG: Message created with ID: {message.id} ===")
        _logger.info(f"=== ALT SUPPORT: Message created with ID: {message.id} ===")
        _logger.info(f"=== ALT SUPPORT: Message model: {message.model} ===")
        _logger.info(f"=== ALT SUPPORT: Message res_id: {message.res_id} ===")
        
        # Check if this is a message in an Alt Support channel
        if message.model == 'discuss.channel':
            print("=== ALT SUPPORT DEBUG: Message is in discuss.channel ===")
            _logger.info("=== ALT SUPPORT: Message is in discuss.channel ===")
            channel = self.env['discuss.channel'].browse(message.res_id)
            _logger.info(f"=== ALT SUPPORT: Channel name: {channel.name} === {channel.id}")
            
            if channel.name.startswith('alt support -') and not self.env.context.get('is_from_client'):
                print("=== ALT SUPPORT DEBUG: Alt Support channel detected! ===")
                _logger.info("=== ALT SUPPORT: Alt Support channel detected! ===")
                self._handle_alt_support_message(message, channel)
            else:
                print("=== ALT SUPPORT DEBUG: Not an Alt Support channel ===")
                _logger.info("=== ALT SUPPORT: Not an Alt Support channel ===")
        else:
            print(f"=== ALT SUPPORT DEBUG: Message model is not discuss.channel: {message.model} ===")
            _logger.info(f"=== ALT SUPPORT: Message model is not discuss.channel: {message.model} ===")
        
        return message

    def _handle_alt_support_message(self, message, channel):
        """Handle messages in Alt Support channels."""
        print(f"=== ALT SUPPORT DEBUG: Handling message {message.id} ===")
        _logger.info(f"=== ALT SUPPORT: Handling message {message.id} ===")
        
        # Get token configuration
        token_config = self.env['ir.config_parameter'].sudo().get_param('alt_support.valid_tokens')
        print(f"=== ALT SUPPORT DEBUG: Raw token config: {token_config} ===")
        _logger.info(f"=== ALT SUPPORT: Raw token config: {token_config} ===")
        
        if not token_config:
            print("=== ALT SUPPORT DEBUG: No token configuration found ===")
            _logger.warning('=== ALT SUPPORT: No token configuration found ===')
            return

        try:
            _logger.info("=== ALT SUPPORT TYPE OF token_config === %s",type(token_config))
            token_config = eval(token_config)  # Convert string to dict
            print(f"=== ALT SUPPORT DEBUG: Parsed token config: {token_config} ===")
            _logger.info(f"=== ALT SUPPORT: Parsed token config: {token_config} ===")
        except Exception as e:
            print(f"=== ALT SUPPORT DEBUG: Failed to parse token configuration: {str(e)} ===")
            _logger.error(f'=== ALT SUPPORT: Failed to parse token configuration: {str(e)} ===')
            return

        # Extract company name from channel name
        channel_parts = channel.name.split(' - ')
        print(f"=== ALT SUPPORT DEBUG: Channel parts: {channel_parts} ===")
        _logger.info(f"=== ALT SUPPORT: Channel parts: {channel_parts} ===")
        
        if len(channel_parts) < 2:
            print(f"=== ALT SUPPORT DEBUG: Invalid channel name format: {channel.name} ===")
            _logger.warning(f'=== ALT SUPPORT: Invalid channel name format: {channel.name} ===')
            return

        company_name = channel_parts[1]
        print(f"=== ALT SUPPORT DEBUG: Extracted company name: {company_name} ===")
        _logger.info(f"=== ALT SUPPORT: Extracted company name: {company_name} ===")
        
        if company_name not in token_config:
            print(f"=== ALT SUPPORT DEBUG: No configuration found for company: {company_name} ===")
            _logger.warning(f'=== ALT SUPPORT: No configuration found for company: {company_name} ===')
            _logger.warning(f'=== ALT SUPPORT: Available companies: {list(token_config.keys())} ===')
            return

        # Get client details
        client_config = token_config[company_name]
        print(f"=== ALT SUPPORT DEBUG: Client config for {company_name}: {client_config} ===")
        _logger.info(f"=== ALT SUPPORT: Client config for {company_name}: {client_config} ===")
        
        client_url = client_config.get('url')
        server_token = client_config.get('server_token')  # Use server token instead of client token
        
        print(f"=== ALT SUPPORT DEBUG: Client URL: {client_url} ===")
        _logger.info(f"=== ALT SUPPORT: Client URL: {client_url} ===")
        _logger.info(f"=== ALT SUPPORT: Server Token: {server_token[:10] if server_token else 'None'}... ===")

        # Prepare message data
        message_data = {
            'message_id': message.message_id,
            'company_name': company_name,
            'author_name': message.author_id.name,
            'channel_type': 'personal' if len(channel_parts) > 2 else 'shared',
            'body': message.body,
            'timestamp': message.date.isoformat() if message.date else None,
            'is_from_server' : True,
            'personal_channel_name' : channel.name
        }
        
        print(f"=== ALT SUPPORT DEBUG: Prepared message data: {message_data} ===")
        _logger.info(f"=== ALT SUPPORT: Prepared message data: {message_data} ===")

        # Build the full URL
        full_url = f"{client_url}/alt-support/receive"
        print(f"=== ALT SUPPORT DEBUG: Sending to full URL: {full_url} ===")
        _logger.info(f"=== ALT SUPPORT: Sending to full URL: {full_url} ===")

        try:
            print(f"=== ALT SUPPORT DEBUG: Making POST request to: {full_url} ===")
            _logger.info(f"=== ALT SUPPORT: Making POST request to: {full_url} ===")
            # _logger.info(f"=== ALT SUPPORT: Headers: Authorization: Bearer {api_token[:10]}... ===")
            _logger.info(f"=== ALT SUPPORT: JSON data: {json.dumps(message_data, indent=2)} ===")
            
            response = requests.post(
                full_url,
                json=message_data,
                headers={
                    'Authorization': f'Bearer {server_token}',
                    'Content-Type': 'application/json'
                },
                timeout=5
            )
            
            print(f"=== ALT SUPPORT DEBUG: Response status: {response.status_code} ===")
            _logger.info(f"=== ALT SUPPORT: Response status: {response.status_code} ===")
            _logger.info(f"=== ALT SUPPORT: Response content: {response.text} ===")
            
            response.raise_for_status()
            print(f"=== ALT SUPPORT DEBUG: Message sent successfully to {company_name} ===")
            _logger.info(f"=== ALT SUPPORT: Message sent successfully to {company_name} ===")
        except requests.exceptions.Timeout:
            print(f"=== ALT SUPPORT DEBUG: Timeout while sending message to client {company_name} ===")
            _logger.error(f'=== ALT SUPPORT: Timeout while sending message to client {company_name} ===')
            raise UserError('Connection to client timed out. Please try again.')
        except requests.exceptions.RequestException as e:
            print(f"=== ALT SUPPORT DEBUG: Failed to send message to client {company_name}: {str(e)} ===")
            _logger.error(f'=== ALT SUPPORT: Failed to send message to client {company_name}: {str(e)} ===')
            raise UserError(f'Failed to send message to client: {str(e)}')
        except Exception as e:
            print(f"=== ALT SUPPORT DEBUG: Unexpected error while sending message to client {company_name}: {str(e)} ===")
            _logger.error(f'=== ALT SUPPORT: Unexpected error while sending message to client {company_name}: {str(e)} ===')
            raise UserError(f'An unexpected error occurred: {str(e)}') 
import json
import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
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

    client_message_id = fields.Integer(string="Client Message Id")

    @api.model
    def create(self, vals):
        """Override create to handle outgoing messages."""
        _logger.info("=== ALT SUPPORT: MailMessage.create called ===")
        
        message = super(MailMessage, self).create(vals)
        
        _logger.info(f"=== ALT SUPPORT: Message Vals: {vals} ===")
        
        # Check if this is a message in an Alt Support channel
        if message.model == 'discuss.channel':
            channel = self.env['discuss.channel'].browse(message.res_id)
            _logger.info(f"=== ALT SUPPORT: Channel name: {channel.name} === {channel}")
            _logger.info("====== channel.name.startswith('alt support -') ======= %s",channel.name)

            if channel.name.startswith('alt support -') and not self.env.context.get('is_from_client'):
                _logger.info("=== ALT SUPPORT: Alt Support channel detected! ===")
                self._handle_alt_support_message(message, channel)

            elif channel.parent_channel_id and channel.parent_channel_id.name and \
                channel.parent_channel_id.name.startswith('alt support -') and not self.env.context.get('is_from_client'):
                _logger.info("=== ALT SUPPORT: Alt Channel Thread detected! ===")
                is_thread = True
                self._handle_alt_support_message(message, channel, is_thread)

            else:
                _logger.info("=== ALT SUPPORT: Not an Alt Support channel Or Thread===")
        else:
            _logger.info(f"=== ALT SUPPORT: Message model is not discuss.channel: {message.model} ===")
        
        return message

    def _handle_alt_support_message(self, message, channel,is_thread=False):
        """Handle messages in Alt Support channels."""
        _logger.info(f"=== ALT SUPPORT: Handling message {message.id} ===")
        
        # Get token configuration
        token_config = self.env['ir.config_parameter'].sudo().get_param('alt_support.valid_tokens')
        _logger.info(f"=== ALT SUPPORT: Raw token config: {token_config} ===")
        
        if not token_config:
            _logger.warning('=== ALT SUPPORT: No token configuration found ===')
            return

        try:
            _logger.info("=== ALT SUPPORT TYPE OF token_config === %s",type(token_config))
            token_config = eval(token_config)  # Convert string to dict
            _logger.info(f"=== ALT SUPPORT: Parsed token config: {token_config} ===")
        except Exception as e:
            _logger.error(f'=== ALT SUPPORT: Failed to parse token configuration: {str(e)} ===')
            return

        if is_thread:
            channel_id = message.res_id
            thead_name = self.env['discuss.channel'].browse(channel_id)
            channel = thead_name.parent_channel_id
            _logger.info("=== ALT SUPPORT THREAD Chanel NAME === %s",channel.name)
        channel_parts = channel.name.split(' - ')
        _logger.info(f"=== ALT SUPPORT: Channel parts: {channel_parts} ===")
        
        if len(channel_parts) < 2:
            _logger.warning(f'=== ALT SUPPORT: Invalid channel name format: {channel.name} ===')
            return

        company_name = channel_parts[1]
        _logger.info(f"=== ALT SUPPORT: Extracted company name: {company_name} ===")
        
        if company_name not in token_config:
            _logger.warning(f'=== ALT SUPPORT: No configuration found for company: {company_name} ===')
            _logger.warning(f'=== ALT SUPPORT: Available companies: {list(token_config.keys())} ===')
            return

        # Get client details
        client_config = token_config[company_name]
        _logger.info(f"=== ALT SUPPORT: Client config for {company_name}: {client_config} ===")
        
        client_url = client_config.get('url')
        server_token = client_config.get('server_token')  # Use server token instead of client token
        
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
            'personal_channel_name' : channel.name,
            'server_message_id' : message.id,
        }

        if is_thread:
            _logger.info("------------- message %s",message)
            _logger.info("------------- message.res_id %s",message.res_id)
            if message.res_id:
                from_message_id = self.env['discuss.channel'].sudo().browse(message.res_id)
            message_data['is_thread'] = True
            message_data['thread_name'] = thead_name.name
            message_data['from_message_id'] = from_message_id.from_message_id.id or False
            message_data['server_channel_id'] = from_message_id.id
        
        _logger.info(f"=== ALT SUPPORT: Prepared message data: {message_data} ===")

        # Build the full URL
        full_url = f"{client_url}/alt-support/receive"
        _logger.info(f"=== ALT SUPPORT: Sending to full URL: {full_url} ===")

        try:
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
            
            _logger.info(f"=== ALT SUPPORT: Response status: {response.status_code} ===")
            _logger.info(f"=== ALT SUPPORT: Response content: {response.text} ===")
            
            response.raise_for_status()
            _logger.info(f"=== ALT SUPPORT: Message sent successfully to {company_name} ===")
        except requests.exceptions.Timeout:
            _logger.error(f'=== ALT SUPPORT: Timeout while sending message to client {company_name} ===')
            raise UserError('Connection to client timed out. Please try again.')
        except requests.exceptions.RequestException as e:
            _logger.error(f'=== ALT SUPPORT: Failed to send message to client {company_name}: {str(e)} ===')
            raise UserError(f'Failed to send message to client: {str(e)}')
        except Exception as e:
            _logger.error(f'=== ALT SUPPORT: Unexpected error while sending message to client {company_name}: {str(e)} ===')
            raise UserError(f'An unexpected error occurred: {str(e)}') 
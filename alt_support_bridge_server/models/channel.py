import json
import requests
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    client_channel_id = fields.Integer(string="Client Channel Id")

    @api.model
    def write(self, vals):
        _logger.info("--- DiscussChannel Write Called From Server--- %s", vals)
        result = super().write(vals)

        # use self (records), not result
        if vals.get('name'):
            for record in self:
                if record.parent_channel_id:
                    try:
                        config = self.env['alt.support.token'].sudo().search([], limit=1)
                        _logger.info(f"=== ALT SUPPORT CLIENT: Found config: {config} ===")

                        if not config:
                            raise UserError('Support server configuration is missing. Please configure the settings in Alt Support Configuration.')
                    
                        url = config.url
                        _logger.info("-------- client_url ----------- %s",url)
                        api_token = config.token

                        if not url or not api_token:
                            raise UserError('Support server configuration is missing. Please set both Server URL and API Token.')

                        message_data = {
                            'name': vals.get('name'),
                            'write_to': record.id,
                        }

                        _logger.info("----------> message_data %s",message_data)
                        headers = {
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {api_token}'
                        }

                        response = requests.post(
                            f'{url}/alt-client/write/thread/name/receive',
                            json=message_data,
                            headers=headers
                        )

                        _logger.info(f"=== ALT SUPPORT CLIENT: Response status: {response} ===")

                    except Exception as e:
                        _logger.error(f'Alt Support Bridge Error: {str(e)}')

        return result

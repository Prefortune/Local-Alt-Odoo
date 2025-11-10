from encodings import charmap
import json
import logging
from math import fabs
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class AltSupportControllerThread(http.Controller):

    @http.route('/alt-support/write/thread/name/receive', type='json', auth='public', csrf=False)
    def receive_message(self, **kwargs):
        """
        API endpoint to update the name of a discuss.channel record.
        Expected JSON body:
        {
            "name": "New Channel Name",
            "write_to": 123  # ID of discuss.channel
        }
        """
        try:
            # ✅ Load JSON body
            data = json.loads(request.httprequest.data)
            _logger.info(f"=== ALT SUPPORT SERVER: THREAD NAME WRITE Received data: {data} ===")

            name = data.get('name')
            apply_to = data.get('write_to')

            # ✅ Validate incoming data
            if not name or not apply_to:
                _logger.warning("Missing 'name' or 'write_to' in request")
                return {
                    'success': False,
                    'error': "Missing required parameters: 'name' and 'write_to'."
                }

            # ✅ Fetch the channel
            channel = request.env['discuss.channel'].sudo().search([
                ('client_channel_id','=',int(apply_to))
            ])

            if not channel.exists():
                channel = request.env['discuss.channel'].sudo().browse(int(apply_to))

            if not channel.exists():
                _logger.warning(f"No channel found for ID Server {apply_to}")
                return {
                    'success': False,
                    'error': f"No discuss.channel found with ID {apply_to}."
                }

            # ✅ Update the channel name
            channel.write({'name': name})
            _logger.info(f"Updated discuss.channel({channel.id}) name to '{name}'")

            return {
                'success': True,
                'channel_id': channel.id,
                'new_name': name,
            }

        except Exception as e:
            _logger.error(f"ALT SUPPORT SERVER ERROR in /alt-support/write/thread/name/receive: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f"Server error: {str(e)}"
            }
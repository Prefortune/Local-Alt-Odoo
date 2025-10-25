from dataclasses import fields

from odoo import api, models,fields
from odoo.addons.base.models.res_users import is_selection_groups
from odoo.addons.mail.models.discuss.res_users import ResUsers
import requests


class ResUsers(models.Model):
    _inherit = "res.users"



    # Load Limited Whatsapp Channel
    def _init_messaging(self):
        """
        This method is overwritten to load the limited WhatsApp Channels.
        """
        res=super()._init_messaging()
        load_channel_limit = int(
            self.env['ir.config_parameter'].sudo().get_param('tus_meta_wa_discuss.whatsapp_channel'))
        limit=load_channel_limit
        if self._context.get('limit', False):
            limit = self._context.get('limit', False)
        #filter only Whatsapp Channels.
        # channels=res.get('channels')[:(limit + 1)]
        new_whatsapp_channels = [i.get('id') for i in res.get('channels') if i.get('channel_type') == 'WpChannels'][:limit + 1]
        new_channels = [i.get('id') for i in res.get('channels') if i.get('channel_type') != 'WpChannels']
        channels = [i for i in res.get('channels') if i.get('id') in new_whatsapp_channels + new_channels]
        res.update({'channels':channels})
        return res

    @api.model
    def get_limit_show(self):
        """
        Load parameters for the JS.
        """
        return {'show': int(self.env['ir.config_parameter'].sudo().get_param('tus_meta_wa_discuss.load_whatsapp_channel')),
                'default_show': int(self.env['ir.config_parameter'].sudo().get_param('tus_meta_wa_discuss.whatsapp_channel'))}


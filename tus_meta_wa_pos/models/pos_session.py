# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_data_process(self, loaded_data):
        """
        This method is overwrite to pass the data of whatsapp template and the provider.
        """
        res = super()._pos_data_process(loaded_data)
        loaded_data['templates'] = self.env['wa.template'].search_read([('model_id.model', '=', 'pos.order')], ['id', 'name', 'model_id', 'provider_id'])
        loaded_data['providers'] = self.env['provider'].search_read([], ['id', 'name'])
        return res

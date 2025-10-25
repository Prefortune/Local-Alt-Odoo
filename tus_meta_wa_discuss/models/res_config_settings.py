from ast import literal_eval

from odoo import api, fields, models,_
from odoo.addons.base.models.ir_config_parameter import IrConfigParameter
from odoo.fields import first


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    not_wa_msgs_btn_in_chatter = fields.Many2many("ir.model","send_wa_msgs_model_rel","model_id","send_wa_msgs_id")
    not_send_msgs_btn_in_chatter = fields.Many2many("ir.model","send_msgs_model_rel","model_id","send_msgs_id")
    load_whatsapp_channel = fields.Integer("Load Whatsapp Channel",readonly=False)
    whatsapp_channel = fields.Char(
        string="Default Whatsapp Channel",
        readonly=False,
        default=5,
    )

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('tus_meta_wa_discuss.not_wa_msgs_btn_in_chatter', self.not_wa_msgs_btn_in_chatter.ids)
        self.env['ir.config_parameter'].sudo().set_param('tus_meta_wa_discuss.not_send_msgs_btn_in_chatter', self.not_send_msgs_btn_in_chatter.ids)
        self.env['ir.config_parameter'].sudo().set_param('tus_meta_wa_discuss.load_whatsapp_channel', self.load_whatsapp_channel)
        self.env['ir.config_parameter'].sudo().set_param('tus_meta_wa_discuss.whatsapp_channel', self.whatsapp_channel)

        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        with_user = self.env['ir.config_parameter'].sudo()
        not_wa_msgs_btn_in_chatter = with_user.get_param('tus_meta_wa_discuss.not_wa_msgs_btn_in_chatter')
        not_send_msgs_btn_in_chatter = with_user.get_param('tus_meta_wa_discuss.not_send_msgs_btn_in_chatter')
        load_whatsapp_channel = with_user.get_param('tus_meta_wa_discuss.load_whatsapp_channel')
        whatsapp_channel = with_user.get_param('tus_meta_wa_discuss.whatsapp_channel')
        res.update(
            not_wa_msgs_btn_in_chatter=[(6, 0, literal_eval(not_wa_msgs_btn_in_chatter))] if not_wa_msgs_btn_in_chatter else False, )
        res.update(
            not_send_msgs_btn_in_chatter=[(6, 0, literal_eval(not_send_msgs_btn_in_chatter))] if not_send_msgs_btn_in_chatter else False, )
        res.update(
            load_whatsapp_channel= load_whatsapp_channel if load_whatsapp_channel else 0
        )
        res.update(
            whatsapp_channel= whatsapp_channel if whatsapp_channel else 0
        )
        return res

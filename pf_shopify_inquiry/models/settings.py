from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    helpdesk_id = fields.Many2one('helpdesk.team', string="Default Helpdesk Team")
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Default Ticket Type")
    tag_id = fields.Many2one('helpdesk.tag', string="Default Tag")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'helpdesk_id': int(self.env['ir.config_parameter'].sudo().get_param('helpdesk.default_team_id', default=False)) or False,
            'ticket_type_id': int(self.env['ir.config_parameter'].sudo().get_param('helpdesk.default_ticket_type_id', default=False)) or False,
            'tag_id': int(self.env['ir.config_parameter'].sudo().get_param('helpdesk.default_tag_id', default=False)) or False,
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('helpdesk.default_team_id', self.helpdesk_id.id or False)
        self.env['ir.config_parameter'].sudo().set_param('helpdesk.default_ticket_type_id', self.ticket_type_id.id or False)
        self.env['ir.config_parameter'].sudo().set_param('helpdesk.default_tag_id', self.tag_id.id or False)

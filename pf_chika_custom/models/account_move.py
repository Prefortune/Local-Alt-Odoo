from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    pos_session_id = fields.Many2one('pos.session', string='POS Session')

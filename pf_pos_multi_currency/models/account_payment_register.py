from odoo import models
class AccountPaymentRegister(models.TransientModel):   
    _inherit = 'account.payment.register'

    def action_create_payments(self):      
        res = super(AccountPaymentRegister,self).action_create_payments()
        active_session = self.env['pos.session'].search(
            [('state', '=', 'opened'),
             ('user_id', '=', self.env.user.id)], limit=1)
        if active_session:
            current_order = self.env['pos.order'].search(
                [('session_id', '=', active_session.id),
                 ('state', '=', 'invoiced')], limit=1)            
            if current_order:
                current_order.write({'is_partial_payment': False})
        return res
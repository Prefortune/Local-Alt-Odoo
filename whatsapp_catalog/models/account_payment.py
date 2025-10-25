from odoo import fields, models


class ComponentsInherit(models.Model):
    _inherit = "account.payment"

    wa_transaction_id = fields.Char('WA Transaction id')
    is_wa_payment = fields.Boolean('Whatsapp Payment')


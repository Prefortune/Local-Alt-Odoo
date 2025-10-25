# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TranzilaPhysicalTerminal(models.Model):
    _inherit = "tranzila.physical.terminal"

    payment_method_id = fields.Many2one(
        "pos.payment.method",
        string="Payment Methods"
    )

    @api.model
    def get_terminals_by_ids(self):
        """
        get terminals in pos
        """
        terminals = self.env["tranzila.physical.terminal"].search([('company_id', '=', self.env.company.id)])
        return [{"id": terminal.id, "name": terminal.pos_id} for terminal in
                terminals]

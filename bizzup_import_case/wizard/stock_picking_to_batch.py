# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class StockPickingToBatch(models.TransientModel):
    _inherit= 'stock.picking.to.batch'

    def attach_pickings(self):
        res = super().attach_pickings()
        self.ensure_one()

        pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids', []))
        print("Pickings:", pickings)

        import_cases = pickings.mapped('import_case_id')
        print("Import Cases:", import_cases)

        # If there's more than one distinct import_case_id, raise error
        if len(import_cases) > 1:
            raise ValidationError(_("You cannot add pickings from multiple Import Cases in the same batch."))
        else:
            batch = self.env['stock.picking.batch'].browse(res.get('res_id'))
            batch.task_id = import_cases.id
        return res

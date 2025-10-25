# -*- coding: utf-8 -*-
# Part of alt AV ltd. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.osv import expression


class StockQuantInherit(models.Model):
    _inherit = "stock.quant"


    def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, qty=0):
    
        result = super(StockQuantInherit ,self)._gather(product_id, location_id, lot_id, package_id, owner_id, strict, qty)
        domain = [
            ('product_id', '=', product_id.id),
        ]
        if not strict:
            if lot_id and len(lot_id) == 1:
                domain = expression.AND([['|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False)], domain])
            if lot_id and len(lot_id) > 1:
                domain = expression.AND([['|', ('lot_id', 'in', lot_id.ids), ('lot_id', '=', False)], domain])
            if package_id:
                domain = expression.AND([[('package_id', '=', package_id.id)], domain])
            if owner_id:
                domain = expression.AND([[('owner_id', '=', owner_id.id)], domain])
            domain = expression.AND([[('location_id', 'child_of', location_id.id)], domain])
        else:
            if lot_id and len(lot_id) == 1:
                domain = expression.AND \
                    ([['|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False)] if lot_id else [('lot_id', '=', False)],
                      domain])
            if lot_id and len(lot_id) > 1:
                domain = expression.AND([['|', ('lot_id', 'in', lot_id.ids), ('lot_id', '=', False)] if lot_id else
                                         [('lot_id', '=', False)], domain])
            domain = expression.AND([[('package_id', '=', package_id and package_id.id or False)], domain])
            domain = expression.AND([[('owner_id', '=', owner_id and owner_id.id or False)], domain])
            domain = expression.AND([[('location_id', '=', location_id.id)], domain])
        # Copy code of _search for special NULLS FIRST/LAST order
        self.check_access_rights('read')
        query = self._where_calc(domain)
        self._apply_ir_rules(query, 'read')
        from_clause = query.from_clause
        where_clause = query.where_clause
        where_str = where_clause and (" WHERE %s" % where_clause) or ''
        res = self._cr.fetchall()
        # No uniquify list necessary as auto_join is not applied anyways...
        quants = self.browse([x[0] for x in res])
        quants = quants.sorted(lambda q: not q.lot_id)

        if quants:
            result.update(quants)
        return result


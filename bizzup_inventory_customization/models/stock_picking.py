# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, models, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def write(self,vals):
        """
        Prevents non-manager users from changing the source or destination location.

        Raises:
            ValidationError: If a non-manager user attempts to change these locations.
        """
        user = self.env.user
        # Check if the user is not a stock manager
        if not user.has_group(
                'stock.group_stock_manager'
                ):
            for record in self:
                if record.picking_type_id.code != 'internal':
                    if record.pos_order_id or record.origin or record.purchase_id or vals.get('pos_order_id',''):
                        continue
                    raise ValidationError(
                            _('You are not allowed to create a new Transfer.')
                        )
                purchase_order = self.env['purchase.order'].search([('name', '=', record.origin)], limit=1)
                if 'location_id' in vals and record.location_id.id != vals[
                    'location_id']:
                    raise ValidationError(
                        _(
                            'You are not allowed to Change Source Location.'
                            )
                        )

                if 'location_dest_id' in vals and record.location_dest_id.id != \
                        vals['location_dest_id']:
                    if purchase_order and purchase_order.is_po_consig:
                        return super(StockPicking,self).write(vals)
                    elif record.sale_id.is_so_consig:
                        return super(StockPicking, self).write(vals)
                    else:
                        raise ValidationError(
                            _(
                                'You are not allowed to Change Destination Location.'
                                )
                            )
        return super(StockPicking,self).write(vals)

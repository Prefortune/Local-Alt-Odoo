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

    @api.model
    def create(self,vals_list):
        """
        Creates a stock picking record with restrictions for non-manager users.
            Args:
                vals_list (dict): Values for creating the stock picking record.
        Returns:
            recordset: The newly created stock picking record.
        Raises:
            ValidationError: If a non-manager user attempts to create a restricted transfer.
        """
        res = super(StockPicking,self).create(vals_list)
        ctx = self.env.context
        if not self.env.user.has_group('stock.group_stock_manager'):
            picking_type_id = vals_list.get('picking_type_id', '')
            picking_type = self.env['stock.picking.type'].browse(picking_type_id)
            if picking_type.sequence_code == 'POS' and not vals_list.get('origin'):
                return res
            else:
                if not ctx.get('login_number'):
                    if res.picking_type_id.code != 'internal':
                        if not res.origin or vals_list.get('login_number'):
                            raise ValidationError(
                                _('You are not allowed to create a new Transfer.')
                            )
        return res

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

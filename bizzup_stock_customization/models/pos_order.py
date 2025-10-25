# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models


class PosOrder(models.Model):
    """
    This class extends the 'pos.order' model to override the
     `_create_order_picking` method.
    """
    _inherit = 'pos.order'

    def _create_order_picking(self):
        """
        Override the method to process consignment transfer after
         creating the order picking.
        """
        res = super(PosOrder,self)._create_order_picking()
        self.picking_ids._process_consign_transfer()
        return res

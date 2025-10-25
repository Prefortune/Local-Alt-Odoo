# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Adds a setting to enable or disable unique lot number checks."""

    _inherit = "res.config.settings"

    disable_unique_lot_check = fields.Boolean(
        string="Disable Unique Lot Check",
        config_parameter="bizzup_lot_serial_customization.disable_unique_lot_check",
    )

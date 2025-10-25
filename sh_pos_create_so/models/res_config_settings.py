# Copyright (C) Softhealer Technologies.
# Part of Softhealer Technologies.


from odoo import models, fields


class ResConfigInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_sh_display_sale_btn = fields.Boolean(
        related="pos_config_id.sh_display_sale_btn", readonly=False)
    pos_select_order_state = fields.Selection(
        related="pos_config_id.select_order_state", readonly=False)

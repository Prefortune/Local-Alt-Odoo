from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class res_company(models.Model):
    _inherit = "res.company"


    module_pos_clover = fields.Boolean(
        string="Clover POS Integration",
        help="The transactions are processed by clover.")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_pos_clover = fields.Boolean(
        string="Clover POS Integration",
        help="The transactions are processed by clover.",
        readonly=False,
        related='company_id.module_pos_clover',
        
        
    )

# -*- coding: utf-8 -*-

#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from hashlib import sha256
from json import dumps
from odoo.tools import float_round
import logging
from dateutil.relativedelta import relativedelta



_logger = logging.getLogger(__name__)


class AccountReceiptLine(models.Model):
    _inherit = "lyg.account.receipt.line"

    tranzila_npay = fields.Char(string="Payments")
    tranzila_fpay = fields.Char(string="First Payment")
    tranzila_spay = fields.Char(string="Other Payment")
    tranzila_line_no = fields.Integer(string="Line no")


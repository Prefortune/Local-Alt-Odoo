# -*- coding: utf-8 -*-
##############################################################################
#
#    Shinefy Technologies Pvt. Ltd.
#    Copyright (C) 2022 Shinefy Technologies.
#    Author: Shinefy Technologies
#    
#    For Module Support : shinefytech@gmail.com  or Skype : shinefytech@gmail.com
#
##############################################################################

from . import models
from odoo.tools import sql, SQL


def uninstall_hook_product(env):
    # self = env['product.template']
    # env.cr.execute(SQL('ALTER TABLE product_template DROP COLUMN company_ids'))
    rules = env['ir.rule'].sudo().search([('name','=','Product multi-company')]).unlink()
    print("REcords are deleting from the product comany ids ----------")

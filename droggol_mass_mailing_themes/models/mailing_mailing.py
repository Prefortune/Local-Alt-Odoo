# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present Droggol Infotech Private Limited. (<https://www.droggol.com/>)

from odoo import models, api

class MassMailing(models.Model):
    _inherit = 'mailing.mailing'

    @api.model
    def dr_module_is_installed(self, module_name):
        if module_name:
            domain = [('name', '=', module_name)]
            module = self.env['ir.module.module'].sudo().search(domain)
            if module and module.state in ['installed', 'to install', 'to upgrade']:
                return True
        return False

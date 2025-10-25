# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    def check_cart_amount(self):
        order = request.website.sale_get_order()
        if not order:
            return False

        # סכימת הכמות הכוללת של כל המוצרים בעגלה
        total_qty = sum(line.product_uom_qty for line in order.order_line)

        # בדיקה אם יש לפחות 30 פריטים
        if total_qty < 30:
            return False
        return True

    def info_message(self):
        ircsudo = self.env['ir.config_parameter'].sudo()
        info_message = ircsudo.get_param(
            'website_sale_checkout_limit.info_message')
        return info_message


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    info_message = fields.Text(string='Message', translate=True)

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'website_sale_checkout_limit.info_message', self.info_message)
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ircsudo = self.env['ir.config_parameter'].sudo()
        res.update({
            'info_message': ircsudo.get_param('website_sale_checkout_limit.info_message', default=''),
        })
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ircsudo = self.env['ir.config_parameter'].sudo()
        info_message = ircsudo.get_param(
            'website_sale_checkout_limit.info_message', default='')
        res.update(
            info_message=info_message,
        )
        return res

# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, _
from odoo.exceptions import ValidationError
from werkzeug.urls import url_join
from datetime import datetime, timedelta


class MarginParameterWizard(models.TransientModel):
    _name = 'profit.approve.wizard'
    _description = 'Profit Approve Wizard'

    order_id = fields.Many2one('sale.order', 'Sale Order')

    def confirm_profit_approve(self):
        """
        Handle approval logic for profitability blocks.

        If the current user is not the manager, send an approval email to the manager.
        If the user is the manager, confirm the sale order.
        """
        sale_order = self.env['sale.order'].browse(self.order_id.id)
        if sale_order.parent_id.name != self.env.user.name:
            if sale_order.manager_approval != True and sale_order.email_sent_manager != True:
                subject = _('Sale Order Approval')
                base_url = self.get_base_url()
                link = url_join(
                    base_url,
                    f"/web#id={sale_order.id}&model=sale.order&view_type=form"
                )
                message = (
                    f"Hello {sale_order.parent_id.name},<br/>"
                    f"Please Approve the Sale Order : {sale_order.name}, of customer : {sale_order.partner_id.name}.<br/>"
                    f"<a href='{link}'>Click here to view the Sale Order</a>."
                )
                mail = self.env['mail.mail'].sudo().create(
                    {
                        'subject': subject,
                        'body_html': message,
                        'email_to': sale_order.parent_id.work_email,
                    }
                )
                mail.send()
                sale_order.write(
                    {
                        'manager_approval': True,
                        'email_sent_manager' : True,
                    })

                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': 'Approve Sale Order',
                    'note': f"Please approve Sale Order {sale_order.name}.",
                    'res_model_id': self.env['ir.model']._get('sale.order').id,  # <-- FIXED MODEL
                    'res_id': sale_order.id,
                    'user_id': sale_order.parent_id.user_id.id,
                })

            else:
                if self.env.lang == 'en_US':
                    raise ValidationError(_('An Email has been sent to your manager to Approve this order.'))
                else:
                    raise ValidationError(_('הודעת אימייל נשלחה למנהל שלך כדי לאשר הזמנה זו.'))
        else:
            sale_order.write({'state': 'sale'})

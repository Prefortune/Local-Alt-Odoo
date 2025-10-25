# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class purchase_order(models.Model):
    _inherit = "purchase.order"

    def inter_company_create_sale_order(self, company):
        """ Create a Sales Order from the current PO (self) """
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise UserError(_(
                'Provide at least one user for inter company relation for %(name)s',
                name=company.name,
            ))

        if not self.env['sale.order'].has_access('create'):
            raise UserError(_(
                "Inter company user of company %(name)s doesn't have enough access rights",
                name=company.name,
            ))

        for rec in self:
            company_partner = rec.company_id.partner_id.with_user(intercompany_uid)
            if company_partner.property_product_pricelist and \
                    rec.currency_id.id != company_partner.property_product_pricelist.currency_id.id:
                raise UserError(_(
                    'You cannot create SO from PO because sale price list currency is different '
                    'than purchase price list currency.\n'
                    'The currency of the SO is obtained from the pricelist of the company partner.\n\n'
                    '(SO currency: %(so_currency)s, Pricelist: %(pricelist)s, Partner: %(partner)s (ID: %(id)s))',
                    so_currency=rec.currency_id.name,
                    pricelist=company_partner.property_product_pricelist.display_name,
                    partner=company_partner.display_name,
                    id=company_partner.id,
                ))

            sale_order_data = rec.sudo()._prepare_sale_order_data(
                rec.name, company_partner, company, rec.dest_address_id.id or False
            )
            sale_order_data['delivery_route_id'] = company_partner.delivery_route_id.id

            inter_user = self.env['res.users'].sudo().browse(intercompany_uid)
            for line in rec.order_line.sudo():
                sale_order_data['order_line'] += [(0, 0, rec._prepare_sale_order_line_data(line, company))]

            sale_order = self.env['sale.order'].with_context(
                allowed_company_ids=inter_user.company_ids.ids,
                in_rental_app=False,
            ).with_user(intercompany_uid).create(sale_order_data)

            msg = _("Automatically generated from %(origin)s of company %(company)s.", origin=self.name,
                    company=rec.company_id.name)
            sale_order.message_post(body=msg)

            # Write vendor reference
            if not rec.partner_ref:
                rec.partner_ref = sale_order.name

            # Only confirm if credit is within limit
            if company.intercompany_document_state == 'posted':
                partner = sale_order.partner_id.with_company(sale_order.company_id)
                credit_limit = partner.credit_limit
                obligo = partner.obligo
                amount_total = sale_order.amount_untaxed + obligo
                if amount_total <= credit_limit:
                    sale_order.with_user(intercompany_uid).action_confirm()

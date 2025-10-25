#############################################################################
# Copyright (C) 2021 Yves Goldberg - Ygol InternetWork - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
##############################################################################

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, \
    pager as portal_pager
from odoo.exceptions import AccessError, MissingError, ValidationError
from collections import OrderedDict
from odoo.http import request
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal as payment_portal


class Portal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'receipt_count' in counters:
            receipt_count = request.env['lyg.account.receipt'].search_count(
                [('state', '=', 'post'),
                 ('receipt_user_id', '=', request.env.user.id)]) \
                if request.env['lyg.account.receipt'].check_access_rights(
                'read', raise_exception=False) else 0
            values['receipt_count'] = receipt_count
        return values

    def _receipt_get_page_view_values(self, receipt, access_token, **kwargs):
        values = {
            'page_name': 'receipt',
            'receipt': receipt,
        }
        return self._get_page_view_values(receipt, access_token, values,
                                          'my_receipt_history', False,
                                          **kwargs)

    @http.route(['/my/receipt', '/my/receipt/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_receipts(self, page=1, date_begin=None, date_end=None,
                           sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        receipts = request.env['lyg.account.receipt'].search(
            [('state', '=', 'post'),
             ('receipt_user_id', '=', request.env.user.id)])
        receipt_count = request.env['lyg.account.receipt'].search_count(
            [('state', '=', 'post'),
             ('receipt_user_id', '=', request.env.user.id)])
        pager = portal_pager(
            url="/my/receipt",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=receipt_count,
            page=page,
            step=self._items_per_page
        )
        request.session['my_receipt_history'] = receipts.ids[:100]
        values = {
            'receipts': receipts,
            'default_url': '/my/receipt',
            'page_name': 'receipt',
            'pager': pager,
        }
        return request.render("lyg_receipt.portal_my_receipts", values)

    @http.route(['/my/receipt/<int:receipt_id>'], type='http', auth="user",
                website=True)
    def portal_my_receipt_detail(self, receipt_id, access_token=None,
                                 report_type=None, download=False, **kw):
        try:
            receipt_sudo = self._document_check_access('lyg.account.receipt',
                                                       receipt_id,
                                                       access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=receipt_sudo,
                                     report_type=report_type,
                                     report_ref='lyg_receipt.action_report_receipt',
                                     download=download)

        values = self._receipt_get_page_view_values(receipt_sudo, access_token,
                                                    **kw)
        return request.render("lyg_receipt.portal_receipt_page", values)

    def _create_transaction(self, *args, provider_reference=None, **kwargs):
        """Create a transaction and assign the partner from the first
         invoice or sale order."""

        res = super()._create_transaction(*args,
                                          provider_reference=provider_reference,
                                          **kwargs)
        if res.invoice_ids:
            partner_id = res.invoice_ids[0].partner_id
            if partner_id:
                res.write({'partner_id': partner_id.id})
        elif res.sale_order_ids:
            partner_id = res.sale_order_ids[0].partner_id
            if partner_id:
                res.write({'partner_id': partner_id.id})

        return res

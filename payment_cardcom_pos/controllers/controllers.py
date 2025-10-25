# -*- coding: utf-8 -*-
# from odoo import http


# class PaymentCardcomPos(http.Controller):
#     @http.route('/payment_cardcom_pos/payment_cardcom_pos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/payment_cardcom_pos/payment_cardcom_pos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('payment_cardcom_pos.listing', {
#             'root': '/payment_cardcom_pos/payment_cardcom_pos',
#             'objects': http.request.env['payment_cardcom_pos.payment_cardcom_pos'].search([]),
#         })

#     @http.route('/payment_cardcom_pos/payment_cardcom_pos/objects/<model("payment_cardcom_pos.payment_cardcom_pos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('payment_cardcom_pos.object', {
#             'object': obj
#         })


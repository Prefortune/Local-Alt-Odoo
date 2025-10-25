# -*- coding: utf-8 -*-
# from odoo import http


# class PfImportOrders(http.Controller):
#     @http.route('/pf_import_orders/pf_import_orders', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pf_import_orders/pf_import_orders/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pf_import_orders.listing', {
#             'root': '/pf_import_orders/pf_import_orders',
#             'objects': http.request.env['pf_import_orders.pf_import_orders'].search([]),
#         })

#     @http.route('/pf_import_orders/pf_import_orders/objects/<model("pf_import_orders.pf_import_orders"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pf_import_orders.object', {
#             'object': obj
#         })


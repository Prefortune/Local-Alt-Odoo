# -*- coding: utf-8 -*-
# from odoo import http


# class PfLinkTracker(http.Controller):
#     @http.route('/pf_link_tracker/pf_link_tracker', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pf_link_tracker/pf_link_tracker/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pf_link_tracker.listing', {
#             'root': '/pf_link_tracker/pf_link_tracker',
#             'objects': http.request.env['pf_link_tracker.pf_link_tracker'].search([]),
#         })

#     @http.route('/pf_link_tracker/pf_link_tracker/objects/<model("pf_link_tracker.pf_link_tracker"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pf_link_tracker.object', {
#             'object': obj
#         })


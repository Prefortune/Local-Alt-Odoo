# -*- coding: utf-8 -*-
# from odoo import http


# class PfChikaReports(http.Controller):
#     @http.route('/pf_chika_reports/pf_chika_reports', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pf_chika_reports/pf_chika_reports/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pf_chika_reports.listing', {
#             'root': '/pf_chika_reports/pf_chika_reports',
#             'objects': http.request.env['pf_chika_reports.pf_chika_reports'].search([]),
#         })

#     @http.route('/pf_chika_reports/pf_chika_reports/objects/<model("pf_chika_reports.pf_chika_reports"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pf_chika_reports.object', {
#             'object': obj
#         })


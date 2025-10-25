# -*- coding: utf-8 -*-
# from odoo import http


# class PfMmbikesCustomization(http.Controller):
#     @http.route('/pf_mmbikes_customization/pf_mmbikes_customization', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pf_mmbikes_customization/pf_mmbikes_customization/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pf_mmbikes_customization.listing', {
#             'root': '/pf_mmbikes_customization/pf_mmbikes_customization',
#             'objects': http.request.env['pf_mmbikes_customization.pf_mmbikes_customization'].search([]),
#         })

#     @http.route('/pf_mmbikes_customization/pf_mmbikes_customization/objects/<model("pf_mmbikes_customization.pf_mmbikes_customization"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pf_mmbikes_customization.object', {
#             'object': obj
#         })


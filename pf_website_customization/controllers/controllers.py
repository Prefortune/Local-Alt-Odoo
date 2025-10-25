# -*- coding: utf-8 -*-
# from odoo import http


# class PfWebsiteCustomization(http.Controller):
#     @http.route('/pf_website_customization/pf_website_customization', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pf_website_customization/pf_website_customization/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pf_website_customization.listing', {
#             'root': '/pf_website_customization/pf_website_customization',
#             'objects': http.request.env['pf_website_customization.pf_website_customization'].search([]),
#         })

#     @http.route('/pf_website_customization/pf_website_customization/objects/<model("pf_website_customization.pf_website_customization"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pf_website_customization.object', {
#             'object': obj
#         })


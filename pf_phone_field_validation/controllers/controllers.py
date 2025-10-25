# -*- coding: utf-8 -*-
# from odoo import http


# class PfPhoneFieldValidation(http.Controller):
#     @http.route('/pf_phone_field_validation/pf_phone_field_validation', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pf_phone_field_validation/pf_phone_field_validation/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pf_phone_field_validation.listing', {
#             'root': '/pf_phone_field_validation/pf_phone_field_validation',
#             'objects': http.request.env['pf_phone_field_validation.pf_phone_field_validation'].search([]),
#         })

#     @http.route('/pf_phone_field_validation/pf_phone_field_validation/objects/<model("pf_phone_field_validation.pf_phone_field_validation"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pf_phone_field_validation.object', {
#             'object': obj
#         })


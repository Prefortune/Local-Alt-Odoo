# from odoo import http
# from odoo.http import request
# from odoo.exceptions import AccessDenied
# import logging
# _logger = logging.getLogger(__name__)

# class AltBatchSplit(http.Controller):
#     @http.route(['/my/orders/<int:order_id>/batch_delivery'], type='http', auth="user", website=True)
#     def show_batch_delivery_page(self, order_id, **kwargs):
#         order = request.env['sale.order'].sudo().browse(order_id)
#         return request.render('alt_batch_split.batch_fill_form', {
#             'order': order,
#         })


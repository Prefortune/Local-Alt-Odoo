# -*- coding: utf-8 -*-
# Part of Creyox Technologies
from odoo import http
import json
from odoo.http import request


class POSController(http.Controller):

    @http.route('/pos/get_advanced_employee_ids', type='json', auth='user')
    def get_advanced_employee_ids(self):
        pos_config = request.env['pos.config'].sudo().search([], limit=1)
        if not pos_config:
            return []

        employee_user_ids = pos_config.advanced_employee_ids.ids

        return employee_user_ids

    @http.route('/pos/validate_employee_pin', type='json', auth='user')
    def validate_employee_pin(self, ):
        data = json.loads(request.httprequest.data)
        pin = data.get("pin")
        allowed_ids = data.get("allowed_ids")
        employees = request.env['hr.employee'].sudo().browse(allowed_ids)

        matched = employees.filtered(lambda e: e.pin == pin)
        if matched:
            return {'success': True, 'employee': {'id': matched.id, 'name': matched.name}}
        return {'success': False}
# -*- coding: utf-8 -*-

import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class TranzilaController(http.Controller):
    _return_url = '/payment/tranzila/checkout_return'

    @http.route(
        _return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False,
        save_session=False
    )
    def tranzila_return(self, **data):
        """ Process the data returned by Tranzila after redirection.
        :param dict data: The feedback data to process
        """
        _logger.info("entering handle_feedback_data with data:\n%s", pprint.pformat(data))
        request.env['payment.transaction'].with_context(online_invoic=True).sudo()._handle_notification_data('tranzila', data)
        return request.redirect('/payment/status')

# -*- coding: utf-8 -*-

import functools
import logging
from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


def fragment_to_query_string(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        kw.pop('debug', False)
        if not kw:
            return """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = l.pathname + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                if (r == l.pathname) {
                    r = '/';
                }
                window.location = r;
            </script></head><body></body></html>"""
        return func(self, *a, **kw)

    return wrapper


class OAuthController(http.Controller):

    @http.route('/facebook_leads/auth', type='http', auth='user', website=False)
    @fragment_to_query_string
    def add_access_token(self, **kw):
        _logger.info('kw: %r', kw)
        if kw.get('access_token'):
            app_id = request.env['facebook.app.credential.info'].search([])[0]
            app_id.write({'facebook_user_access_token': kw.get('access_token', '')})
            action_id = request.env.ref('rcs_facebook_leads_generate.action_facebook_app_credential')
            return request.redirect('/web#id=%s&action=%s&model=%s&view_type=form' % (app_id.id, action_id.id, app_id._name))

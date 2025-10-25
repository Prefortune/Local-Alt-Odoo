# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo import SUPERUSER_ID, _, http
from odoo.exceptions import UserError
from odoo.http import request, Response
from odoo.tools import replace_exceptions
import base64
import requests
import logging



logger = logging.getLogger(__name__)



class lvSnp(http.Controller):

    @http.route('/player/local/<int:id>',type='http', auth='public',website=True)
    def player(self, id=None,**kwargs):
        rqUrl = '/video/content/{id}'.format(id=id)
        autoplay = kwargs.get('autoplay')=='1'
        controls = kwargs.get('controls')=='1'
        loop = kwargs.get('loop')=='1'
        video_params = {
            'auto_play': autoplay,
            'controls': controls,
            'loop': loop
        }
        return http.request.render('lv_snp.snp-player', {'data': rqUrl,**video_params})

    @http.route('/video/content/<int:id>', type='http', auth="public")
    def content_common(self, id=None, mimetype=None):
        with replace_exceptions(UserError, by=request.not_found()):
            record = request.env['ir.binary']._find_record(None, 'ir.attachment', id and int(id), None)
            stream = request.env['ir.binary']._get_stream_from(record, 'raw', None, 'name', mimetype)
        send_file_kwargs = {'as_attachment': False}
        res = stream.get_response(**send_file_kwargs)
        res.headers['Content-Security-Policy'] = "default-src 'self'"
        return res


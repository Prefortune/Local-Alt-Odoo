# file: custom_module/controllers/main.py
from odoo import http
from werkzeug.exceptions import NotFound
from odoo.http import request
from odoo.addons.mail.models.discuss.mail_guest import add_guest_to_context
from odoo.addons.mail.controllers.webclient import WebclientController


class CustomWebclientController(WebclientController):


    @http.route("/mail/init_messaging", methods=["POST"], type="json", auth="public")
    @add_guest_to_context
    def mail_init_messaging(self, context=None):
        """
        This method is overwritten to load the limited WhatsApp Channels.
        """
        if not request.env.user._is_public():
            if context:
                request.update_context(allowed_company_ids=context.get('allowed_company_ids'))
            if not context:
                context = {}
            return request.env.user.sudo(False).with_context(context)._init_messaging()
        guest = request.env["mail.guest"]._get_guest_from_context()
        if guest:
            return guest._init_messaging()
        raise NotFound()
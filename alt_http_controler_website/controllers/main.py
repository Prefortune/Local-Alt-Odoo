from odoo import http
from odoo.http import request
import re
import logging

_logger = logging.getLogger(__name__)

class DomainRedirect(http.Controller):
    @http.route('/', type='http', auth="public", website=True)
    def domain_redirect(self, **kw):
        # Get the host from the request
        host = request.httprequest.host.lower()
        _logger.info(f"Domain redirect request received for host: {host}")
        
        # Domain configuration
        domain_config = {
            'amflow.co.il': 'https://www.amflow.co.il',
            'cervelo.co.il': 'https://www.cervelo.co.il'
        }
        
        # Remove www. if present for comparison
        clean_host = re.sub(r'^www\.', '', host)
        _logger.debug(f"Cleaned host: {clean_host}")
        
        # Check if the domain is in our configuration
        if clean_host in domain_config:
            _logger.info(f"Found domain configuration for: {clean_host}")
            redirect_url = f"{domain_config[clean_host]}{request.httprequest.path}"
            _logger.info(f"Redirecting to: {redirect_url}")
            return request.redirect(redirect_url, code=301)
        
        _logger.info(f"No specific configuration found for {host}, continuing with normal routing")
        # If no specific configuration found, continue with normal Odoo routing
        return request.redirect('/web', code=301) 
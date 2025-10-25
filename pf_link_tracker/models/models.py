
from odoo import models, fields, api
from urllib.parse import urlparse
from werkzeug import urls
import logging
_logger = logging.getLogger(__name__)

class LinkTracker(models.Model):
    _inherit = 'link.tracker'

    pf_short_url_host = fields.Char(string='PF Host of the short URL', compute='_compute_pf_short_url_host')

    def get_base_domain(self,link: str) -> str:
        parsed = urlparse(link)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    @api.depends('url')
    def _compute_pf_short_url_host(self):
        for tracker in self:
            if tracker.url:
                tracker.pf_short_url_host = self.get_base_domain(tracker.url)  + '/r/'
            else:
                tracker.pf_short_url_host = ''





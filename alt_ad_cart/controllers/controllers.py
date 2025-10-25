from math import fabs
from odoo import http
from odoo.http import request
from markupsafe import Markup
import html  # built-in module to unescape HTML entities
import logging
_logger = logging.getLogger(__name__)

class AltAdCardController(http.Controller):

    @http.route('/alt_ad_card/get_ads', type='json', auth='public', website=True)
    def get_ads(self,is_mobile):

        if is_mobile:
            
            domain = [('alt_active', '=', True),('alt_website','=',request.website.id),('alt_device_type','!=','desktop')]
        else:
            domain = [('alt_active', '=', True),('alt_website','=',request.website.id),('alt_device_type','!=','mobile')]

        ads = request.env['alt.ad.card'].sudo().search(domain, order='alt_priority desc')
        _logger.info("----------> ads %s",ads)

        result = []
        for ad in ads:
            # Step 1: Strip data-oe wrappers if any
            raw_html = ad.alt_content_html or ""

            # Step 2: Unescape entities like &lt; and &gt;
            decoded_html = html.unescape(raw_html)

            # Step 3: Optional: ensure it's safe for rendering
            safe_html = Markup(decoded_html)

            result.append({
                'id': ad.id,
                'name': ad.name,
                'html': safe_html,  # now contains clean HTML tags
                'position_type': ad.alt_position_type,
                'display_every': ad.alt_display_every or 4,
                'priority': ad.alt_priority or 0,
                'category_ids' : ad.alt_category_ids.ids or False,
                'tags_ids' : ad.alt_tag_ids.ids or False
            })
        _logger.info("----> result %s",result)
        return result

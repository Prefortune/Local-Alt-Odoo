from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
import json


class AltSearchbarController(http.Controller):
    
    @http.route('/alt/searchbar/config', type='json', auth='public', website=True)
    def get_searchbar_config_json(self):
        """Get searchbar configuration for current website - JSON RPC"""
        return self._get_searchbar_config()
    
    @http.route('/alt/searchbar/config', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def get_searchbar_config_http(self):
        """Get searchbar configuration for current website - HTTP POST"""
        # print("=== GETTING SEARCHBAR CONFIG ===")
        try:
            config_data = self._get_searchbar_config()
            return json.dumps(config_data)
        except Exception as e:
            # print("Error getting searchbar config:", str(e))
            return json.dumps({'error': str(e)})
    
    def _get_searchbar_config(self):
        """Get searchbar configuration for current website"""
        try:
            website = request.website
            if not website:
                print("No website found")
                return {'error': 'No website found'}
            
            print("Getting config for website:", website.id)
            
            # Get active configuration
            config_model = request.env['alt.searchbar.config']
            config = config_model.get_active_config(website.id)
            
            if not config:
                print("No active configuration found")
                return {
                    'categories': [],
                    'attributes': [],
                    'tags': [],
                    'show_price_filter': True,
                    'price_ranges': config_model.get_price_ranges()
                }
            
            print("Found config:", config.name)
            
            # Get data
            categories = config.get_categories_data()
            attributes = config.get_attributes_data()
            tags = config.get_tags_data()
            price_ranges = config.get_price_ranges()
            
            print("Categories:", len(categories))
            print("Attributes:", len(attributes))
            print("Tags:", len(tags))
            print("Price ranges:", len(price_ranges))
            
            return {
                'categories': categories,
                'attributes': attributes,
                'tags': tags,
                'show_price_filter': config.show_price_filter,
                'price_ranges': price_ranges
            }
            
        except Exception as e:
            print("Error in _get_searchbar_config:", str(e))
            return {'error': str(e)}
    
    @http.route('/alt/searchbar/should_show', type='json', auth='public', website=True)
    def should_show_searchbar(self):
        """Check if searchbar should be shown for current website"""
        try:
            website = request.website
            if not website:
                return False
            
            config_model = request.env['alt.searchbar.config']
            config = config_model.get_active_config(website.id)
            
            return bool(config and config.is_active)
            
        except Exception as e:
            print("Error checking if should show searchbar:", str(e))
            return False
    
    @http.route('/alt/searchbar/debug', type='http', auth='public', website=True, methods=['GET'])
    def debug_searchbar(self):
        """Debug endpoint to check what's happening with filtering"""
        try:
            print("=== DEBUG SEARCHBAR ===")
            print("Request args:", request.httprequest.args)
            print("Request params:", request.params)
            
            # Check if we're on shop page
            if request.httprequest.path == '/shop':
                print("On shop page")
                print("Category:", request.params.get('category'))
                print("Min price:", request.params.get('min_price'))
                print("Max price:", request.params.get('max_price'))
                print("Attribute values:", request.params.getlist('attribute_value'))
                print("Tags:", request.params.get('tags'))
            else:
                print("Not on shop page, path:", request.httprequest.path)
            
            return json.dumps({
                'args': dict(request.httprequest.args),
                'params': dict(request.params),
                'path': request.httprequest.path
            })
            
        except Exception as e:
            print("Error in debug:", str(e))
            return json.dumps({'error': str(e)}) 
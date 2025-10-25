import logging
from odoo import http
from odoo.http import request, Response
from odoo.tools import misc
import secrets
import re
_logger = logging.getLogger(__name__)
import json


class WebsiteFormCartLink(http.Controller):
    """Controller to handle website form submissions and cart assignment"""

    @http.route(['/form/login/success'], type='http', auth="user", methods=['GET'], website=True)
    def success_page(self, **kwargs):
        """Render a success page for the logged-in user's partner using a QWeb template"""
        _logger.info("kwargs --------> %s",kwargs)
        user = request.env.user
        partner = user.sudo().partner_id
        if not partner or not partner.exists():
            return request.redirect('/')
        last_url = request.httprequest.headers.get('Referer', '/')
        _logger.info("-- last_url -- %s",last_url)
        return request.redirect(last_url)
        # return request.render('alt_cart_web_assign.success_page', {'partner': partner})

    @http.route(['/website/form/<string:model_name>'], type='http', auth="public", methods=['POST'], csrf=True, website=True)
    def website_form(self, model_name, **kwargs):
        """Handle website form submission and assign cart to customer"""
        
        # בדיקה שהקוד שלנו מופעל
        _logger.info(f"Custom form received for model {model_name} with data: {kwargs}")
        
        try:
            # Handle form submission based on model
            if model_name == 'res.partner':
                # Process the form data and create/update partner
                partner = self._process_partner_form(**kwargs)
                
                if partner:
                    # Try to link cart to partner
                    self._link_cart_to_partner(partner)
                    
                    # Try to create user account and login
                    response =  self._handle_user_creation(partner)
                    return response    
            else:
                _logger.warning(f"Form handling not implemented for model: {model_name}")
                return request.redirect('/')
                
        except Exception as e:
            _logger.error(f"Error handling form: {str(e)}")
            # הצגת הודעת שגיאה HTML פשוטה

    def _process_partner_form(self, **kwargs):
        """Process partner form data and create/update partner"""
        try:
            session_data = request.env["ir.http"].get_frontend_session_info()
            _logger.info("------- session data---------- %s",session_data)
            kwargs_phone = kwargs.get('phone', '')
            phone = re.sub(r'[^0-9+]', '', kwargs_phone)
            if phone:
                geoip_phone_code = session_data.get('geoip_phone_code')
                if geoip_phone_code:
                     # Case 1: Already correct (+972...)
                    if phone.startswith(f'+{geoip_phone_code}'):
                        pass  # keep as is

                    # Case 2: Starts with 972 (missing +)
                    elif phone.startswith(str(geoip_phone_code)):
                        phone = f'+{phone}'

                    # # Case 3: Starts with 0 (local format)
                    # elif phone.startswith('0'):
                    #     phone = f'+{geoip_phone_code}{phone[1:]}'

                    # Case 4: Anything else → just prepend country code
                    else:
                        phone = f'+{geoip_phone_code}{phone}'

            # Create partner from form data
            partner_vals = {
                'name': kwargs.get('name', ''),
                'email': kwargs.get('email', ''),
                'phone': phone,
                'mobile' : phone,
                'street': kwargs.get('street', ''),
                'city': kwargs.get('city', ''),
                'zip': kwargs.get('zip', ''),
                'country_id': int(kwargs.get('country_id')) if kwargs.get('country_id') else False,
                'category_id' : [(4, int(kwargs.get('category_id')))] if kwargs.get('category_id') else False
            }
            _logger.info("--- partner_vals --- getting from website %S", partner_vals)
            
            # Remove empty values
            partner_vals = {k: v for k, v in partner_vals.items() if v}
            
            # Check if phone is provided (required for cart linking)
            if not partner_vals.get('phone'):
                _logger.error("Phone is required for partner creation and cart linking")
                return None
            
            # Check if partner already exists by phone (more reliable than email)
            existing_partner = request.env['res.partner'].sudo().search([
                ('phone', '=', partner_vals['phone'])
            ], limit=1)
            
            if existing_partner:
                partner = existing_partner
                _logger.info(f"Using existing partner by phone: {partner.name} ({partner.phone})")
                
                # Update existing partner with new information if provided
                update_vals = {}
                for field, value in partner_vals.items():
                    if field != 'phone' and value and (not getattr(partner, field, False) or getattr(partner, field, '') != value):
                        update_vals[field] = value
                
                if update_vals:
                    partner.sudo().write(update_vals)
                    _logger.info(f"Updated existing partner with new information: {update_vals}")
            else:
                # Create new partner
                partner = request.env['res.partner'].sudo().create(partner_vals)
                _logger.info(f"Created new partner: {partner.name} ({partner.phone})")
            
            return partner
            
        except Exception as e:
            _logger.error(f"Error processing partner form: {str(e)}")
            return None

    def _link_cart_to_partner(self, partner):
        """Link current cart to partner"""
        try:
            order = request.website.sale_get_order(force_create=True)
            if order:
                order = order.sudo()
                order.partner_id = partner
                order.partner_invoice_id = partner
                order.partner_shipping_id = partner

                # order.sudo()._update_address(partner.id, {
                #     'partner_id',
                #     'partner_invoice_id',
                #     'partner_shipping_id',
                # })
                _logger.info(f"[Cart Linked] Partner '{partner.name}' (Phone: {partner.phone}) linked to order {order.name}")
            else:
                _logger.warning("No active order found when trying to link partner")
        except Exception as e:
            _logger.error(f"Error linking cart to partner: {str(e)}")

    def _handle_user_creation(self, partner):
        """Handle user account creation and login"""
        try:
            # Check if user already exists with this phone
            password = secrets.token_urlsafe(12)
            existing_user = request.env['res.users'].sudo().search([
                ('partner_id.phone', '=', partner.phone)
            ], limit=1)
            
            if existing_user:
                _logger.info(f"User already exists for phone {partner.phone}, logging in existing user")
                user = existing_user
                user.password = password
            else:
                # Check if partner already has user_ids (created by auth_signup)
                if partner.user_ids:
                    user = partner.user_ids[0]
                    _logger.info(f"Using existing user from partner.user_ids: {user.name}")
                else:
                    # Create user account manually
                    user_vals = {
                        'name': partner.name,
                        'email': partner.email or f"{partner.phone}@phone.user",
                        'login': partner.email or f"{partner.phone}@phone.user",
                        'partner_id': partner.id,
                        'active': True,
                        'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
                        'password' : password
                    }                    
                    # Create user
                    user = request.env['res.users'].sudo().with_context(user_for_cart_assing = True).create(user_vals)
                    _logger.info(f"Created new user account for partner: {partner.name} " f"(Phone: {partner.phone}) Password: {user.password}")
   
            # Try to login the user
            try:
                request.env.cr.commit() 
                credential = {'login': user.login, 'password': password, 'type': 'password'}
                _logger.info("User credential - %s",credential)
                # auth_info = request.session.authenticate(request.db, credential)
                login = user.login
                auth_info = request.session.authenticate(request.db, login , password)

                _logger.info(f"User {user.name} authenticated successfully, Auth =  {auth_info}")

                # return {'id' : user.partner_id.id}

                return json.dumps({'id': user.partner_id.id})
                
                # return request.redirect('/shop')
                # if auth_info['uid']:
                #     return request.redirect('/shop')
                # else:
                #     return request.redirect('/home')


                # return user

                # Set session user directly
                # request.session.uid = user.id
                # request.session.login = user.login
                # request.session.context = request.env['res.users'].context_get()
                
                # # Update session with user info
                # request.session['db'] = request.db
                # request.session['user_context'] = request.env['res.users'].context_get()
                # _logger.info(f"User {user.name} logged in successfully")
                
                
            except Exception as login_error:
                _logger.error(f"Error logging in user: {str(login_error)}")
                
        except Exception as e:
            _logger.error(f"Error in user creation: {str(e)}")

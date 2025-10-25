from odoo import http,_
from odoo.http import request , route
import json
import logging
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)
from odoo.tools import str2bool , clean_context

from odoo.addons.website_sale.controllers.delivery import Delivery
from odoo.addons.website_sale.controllers.main import WebsiteSale

class UpdateAddress(WebsiteSale):

    def _check_cart_and_addresses(self, order_sudo):
        """ Check whether the cart and its addresses are valid, and redirect to the appropriate page
        if not.

        :param sale.order order_sudo: The cart to check.
        :return: None if both the cart and its addresses are valid; otherwise, a redirection to the
                 appropriate page.
        """
        if redirection := self._check_cart(order_sudo):
            return redirection

        if redirection := self._check_addresses(order_sudo):
            return redirection

    def _check_cart(self, order_sudo):
        """ Check whether the cart is a valid, and redirect to the appropriate page if not.

        The cart is only valid if:

        - it exists and is in the draft state;
        - it contains products (i.e., order lines);
        - either the user is logged in, or public orders are allowed.

        :param sale.order order_sudo: The cart to check.
        :return: None if the cart is valid; otherwise, a redirection to the appropriate page.
        """
        # Check that the cart exists and is in the draft state.
        if not order_sudo or order_sudo.state != 'draft':
            request.session['sale_order_id'] = None
            request.session['sale_transaction_id'] = None
            return request.redirect('/shop')

        # Check that the cart is not empty.
        if not order_sudo.order_line:
            return request.redirect('/shop/cart')

        # Check that public orders are allowed.
        if request.env.user._is_public() and request.website.account_on_checkout == 'mandatory':
            return request.redirect('/web/login?redirect=/shop/checkout')

    def _check_addresses(self, order_sudo):
        """ Check whether the cart's addresses are complete and valid.

        The addresses are complete and valid if:

        - at least one address has been added;
        - the delivery address is complete;
        - the billing address is complete.

        :param sale.order order_sudo: The cart whose addresses to check.
        None if the cart is valid; otherwise, a redirection to the appropriate page.
        :return: None if the cart's addresses are complete and valid; otherwise, a redirection to
                 the appropriate page.
        """
        # Check that an address has been added.

        # partner = order_sudo.partner_id
        partner = order_sudo.partner_id if not order_sudo.partner_id.id == 8 else False
        if partner:
            # required_fields = [
            #         partner.street,
            #         # partner.city,
            #     ]
            required_fields = False if partner.street else True
        else:
            required_fields = False
        # required_fields = [
        #         # partner.street,
        #         partner.street2,
        #         partner.city,
        #     ]

        _logger.info("---- _check_addresses ---- %s",required_fields)
        _logger.info("---- order_sudo._is_anonymous_cart() ---- %s",order_sudo._is_anonymous_cart())

        if order_sudo._is_anonymous_cart() or required_fields:
            _logger.info("return request.redirect('/shop/address')")
            return request.redirect('/shop/address')
        

        # Check that the delivery address is complete.
        delivery_partner_sudo = order_sudo.partner_shipping_id
        _logger.info("------ order_sudo.only_services ------------ %s",order_sudo.only_services)
        _logger.info("------ self._check_delivery_address(delivery_partner_sudo) ------------ %s",self._check_delivery_address(delivery_partner_sudo))
        _logger.info("------ delivery_partner_sudo._can_be_edited_by_current_customer(order_sudo, 'delivery') ------------ %s",delivery_partner_sudo._can_be_edited_by_current_customer(order_sudo, 'delivery'))

        if required_fields:
            _logger.info("--------- if not required_fields -----------------")
            if (
                not order_sudo.only_services
                and not self._check_delivery_address(delivery_partner_sudo)
                and delivery_partner_sudo._can_be_edited_by_current_customer(order_sudo, 'delivery')
            ):
                return request.redirect(
                    f'/shop/address?partner_id={delivery_partner_sudo.id}&address_type=delivery'
                )
        if required_fields:
        # Check that the billing address is complete.
            invoice_partner_sudo = order_sudo.partner_invoice_id
            if (
                not self._check_billing_address(invoice_partner_sudo)
                and invoice_partner_sudo._can_be_edited_by_current_customer(order_sudo, 'billing')
            ):
                return request.redirect(
                    f'/shop/address?partner_id={invoice_partner_sudo.id}&address_type=billing'
                )

    @route(
        '/shop/checkout', type='http', methods=['GET'], auth='public', website=True, sitemap=False
    )
    def shop_checkout(self, try_skip_step=None, **query_params):
        _logger.info("--- from custom code is it calling $$$$$$$ shop_checkout --- is calle -----")
        """ Display the checkout page.

        :param str try_skip_step: Whether the user should immediately be redirected to the next step
                                  if no additional information (i.e., address or delivery method) is
                                  required on the checkout page. 'true' or 'false'.
        :param dict query_params: The additional query string parameters.
        :return: The rendered checkout page.
        :rtype: str
        """
        try_skip_step = str2bool(try_skip_step or 'false')
        order_sudo = request.website.sale_get_order()
        request.session['sale_last_order_id'] = order_sudo.id

        if redirection := self._check_cart_and_addresses(order_sudo):
            _logger.info("---- 1 redirection --- %s",redirection)
            return redirection

        checkout_page_values = self._prepare_checkout_page_values(order_sudo, **query_params)

        can_skip_delivery = True  # Delivery is only needed for deliverable products.
        if order_sudo._has_deliverable_products():
            can_skip_delivery = False
            available_dms = order_sudo._get_delivery_methods()
            checkout_page_values['delivery_methods'] = available_dms
            if delivery_method := order_sudo._get_preferred_delivery_method(available_dms):
                rate = delivery_method.rate_shipment(order_sudo)
                if (
                    not order_sudo.carrier_id
                    or not rate.get('success')
                    or order_sudo.amount_delivery != rate['price']
                ):
                    order_sudo._set_delivery_method(delivery_method, rate=rate)

        if try_skip_step and can_skip_delivery:
            _logger.info("---- try_skip_step and can_skip_delivery --------- %s %s",try_skip_step , can_skip_delivery)
            return request.redirect('/shop/confirm_order')

        _logger.info("request.render('website_sale.checkout', checkout_page_values) --- %s",checkout_page_values)
        return request.render('website_sale.checkout', checkout_page_values)

    @http.route(
        '/shop/address', type='http', auth='public', website=True, sitemap=False
    )
    def shop_address(self, partner_id=None, address_type='billing', use_delivery_as_billing=None, **query_params):

        _logger.info("------- shop/address---------- called from custom module")
        """ Display the address form.

        A partner and/or an address type can be given through the query string params to specify
        which address to update or create, and its type.

        :param str partner_id: The partner whose address to update with the address form, if any.
        :param str address_type: The type of the address: 'billing' or 'delivery'.
        :param str use_delivery_as_billing: Whether the provided address should be used as both the
                                            delivery and the billing address. 'true' or 'false'.
        :param dict query_params: The additional query string parameters forwarded to
                                  `_prepare_address_form_values`.
        :return: The rendered address form.
        :rtype: str
        """
        partner_id = partner_id and int(partner_id)
        use_delivery_as_billing = str2bool(use_delivery_as_billing or 'false')
        order_sudo = request.website.sale_get_order()
        is_enable_guest_checkout = request.website.enable_guest_checkout
        is_enable_company_vat_visible = request.website.enable_company_vat_visible
        is_enable_set_delivery_date = request.website.enable_set_delivery_date

        # _logger.info("is_enable_guest_checkout ------------------- %s", is_enable_guest_checkout)

        if redirection := self._check_cart(order_sudo):
            return redirection

        # Retrieve the partner whose address to update, if any, and its address type.
        partner_sudo, address_type = self._prepare_address_update(
            order_sudo, partner_id=partner_id, address_type=address_type
        )

        if partner_sudo:  # If editing an existing partner.
            use_delivery_as_billing = (
                order_sudo.partner_shipping_id == order_sudo.partner_invoice_id
            )

        # Render the address form.
        address_form_values = self._prepare_address_form_values(
            order_sudo,
            partner_sudo,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            **query_params
        )
        
        address_form_values.update({
              'delivery_methods': request.env['delivery.carrier'].sudo().search([
                                    ('is_published','=',True), 
                                    '|',
                                    ('website_id', '=', request.website.id), # Current Site
                                    ('website_id', '=', False),  # Global
                                ]),
        })
        _logger.info("@@@@@@@@@@ order_sudo.partner_id @@@@@@@@@@@ %s",order_sudo.partner_id)
        partner = order_sudo.partner_id if not order_sudo.partner_id.id == 8 else False
        if partner:
            required_fields = False if partner.street else True
            # required_fields = [
            #         partner.street
            #     ]
        else:
            required_fields = False

        address_form_values.update({
            'is_enable_guest_checkout' : is_enable_guest_checkout,
            'is_enable_company_vat_visible' : is_enable_company_vat_visible,
            'is_enable_set_delivery_date' : is_enable_set_delivery_date,
            'required_fields' : required_fields,
            'is_partner_sudo': partner,  # Pass the partner object,
            'is_partner_sudo_id' : partner.id if partner else False
        })
        _logger.info("address_form_values %s",address_form_values)
        return request.render('website_sale.address', address_form_values)

    @route(
        '/shop/address/submit', type='http', methods=['POST'], auth='public', website=True,
        sitemap=False
    )
    def shop_address_submit(
        self, partner_id=None, address_type='billing', use_delivery_as_billing=None, callback=None,
        required_fields=None, **form_data
    ):
        """ Create or update an address.

        If it succeeds, it returns the URL to redirect (client-side) to. If it fails (missing or
        invalid information), it highlights the problematic form input with the appropriate error
        message.

        :param str partner_id: The partner whose address to update with the address form, if any.
        :param str address_type: The type of the address: 'billing' or 'delivery'.
        :param str use_delivery_as_billing: Whether the provided address should be used as both the
                                            billing and the delivery address. 'true' or 'false'.
        :param str callback: The URL to redirect to in case of successful address creation/update.
        :param str required_fields: The additional required address values, as a comma-separated
                                    list of `res.partner` fields.
        :param dict form_data: The form data to process as address values.
        :return: A JSON-encoded feedback, with either the success URL or an error message.
        :rtype: str
        """
        _logger.info("shop_address_submit called with partner_id: %s, address_type: %s, use_delivery_as_billing: %s, callback: %s, required_fields: %s",
                     partner_id, address_type, use_delivery_as_billing, callback, required_fields)

        _logger.info("Form data received: %s", form_data)
        
        # return False
        gretting_note = ''
        delivery_note = ''
        is_write_partner_id = form_data.get('is_partner_sudo_id')
        

        if form_data.get('guest_greeting_card_input'):
            gretting_note = form_data['guest_greeting_card_input']

        if form_data.get('guest_delivery_note_text'):
            delivery_note = form_data['guest_delivery_note_text']
        
        if not form_data.get('country_id'):
            Israel = request.env['res.country'].sudo().search([('code', '=', 'IL')], limit=1)
            if Israel:
                form_data['country_id'] = Israel.id

        
        order_sudo = request.website.sale_get_order()

        if order_sudo:
            order_sudo.greeting_card = gretting_note
            order_sudo.delivery_note = delivery_note
            
        if redirection := self._check_cart(order_sudo):
            _logger.info("redirection := self._check_cart(order_sudo): ---- %s",redirection)
            return json.dumps({'redirectUrl': redirection.location})


        partner_sudo, address_type = self._prepare_address_update(
            order_sudo, partner_id=partner_id and int(partner_id), address_type=address_type
        )
        use_delivery_as_billing = str2bool(use_delivery_as_billing or 'false')
        required_fields = required_fields or ''

        # Parse form data into address values, and extract incompatible data as extra form data.
        address_values, extra_form_data = self._parse_form_data(form_data)
        _logger.info("--- address_values, extra_form_data = self._parse_form_data(form_data)--- %s %s",address_values, extra_form_data )

        is_anonymous_cart = order_sudo._is_anonymous_cart()
        is_main_address = is_anonymous_cart or order_sudo.partner_id.id == partner_sudo.id

        if is_write_partner_id:
            write_partner_id = request.env['res.partner'].sudo().browse(int(is_write_partner_id))

            self._complete_address_values(
                address_values, address_type, use_delivery_as_billing, order_sudo
            )
            write_partner_id.sudo().write({
                'phone' : form_data.get('personal_phone'),
                'street' : form_data.get('street'),
                'street2' : form_data.get('street2'),
                'city' : form_data.get('city'),
                'zip' : form_data.get('zip'),
                'country_id' : form_data.get('country_id'),
                'vat' : form_data.get('personal_vat'),
                'company_name' : form_data.get('company_name')
            })

            return json.dumps({
            'redirectUrl': '/shop/checkout',
        })



        # Validate the address values and highlights the problems in the form, if any.
        invalid_fields, missing_fields, error_messages = self._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            is_main_address=is_main_address,
            **extra_form_data,
        )
        if error_messages:
            return json.dumps({
                'invalid_fields': list(invalid_fields | missing_fields),
                'messages': error_messages,
            })

        is_new_address = False
        if not partner_sudo:  # Creation of a new address.
            is_new_address = True
            self._complete_address_values(
                address_values, address_type, use_delivery_as_billing, order_sudo
            )
            create_context = clean_context(request.env.context)
            create_context.update({
                'tracking_disable': True,
                'no_vat_validation': True,  # Already verified in _validate_address_values
            })
            # this is custom added for update mobile same as phone
            address_values.update({
                'mobile' : address_values.get('phone',False)
            })
            _logger.info("Create context: %s", create_context)
            _logger.info("Creating new partner with values: %s", address_values)
            #return False
            partner_sudo = request.env['res.partner'].sudo().with_context(
                create_context
            ).create(address_values)

            #create dummy shipping address for above partner_sudo without checking address_type
            # same_address = form_data.get('same_address', 'false').lower() != 'on'
            # if same_address:
            #     Israel = request.env['res.country'].sudo().search([('code', '=', 'IL')], limit=1)
            #     State = request.env['res.country.state'].sudo().search([('code', '=', 'israel')], limit=1)
            #     dummy_shipping_address = address_values.copy()
            #     dummy_shipping_address['type'] = 'delivery'
            #     dummy_shipping_address['name'] = form_data.get('invoice_name')
            #     dummy_shipping_address['email'] = form_data.get('invoice_email')
            #     dummy_shipping_address['phone'] = form_data.get('invoice_phone')
            #     dummy_shipping_address['street'] = form_data.get('invoice_street')
            #     dummy_shipping_address['street2'] = form_data.get('invoice_street2')
            #     dummy_shipping_address['city'] = form_data.get('invoice_city')
            #     dummy_shipping_address['zip'] = form_data.get('invoice_zip')
            #     dummy_shipping_address['country_id'] = Israel.id
            #     dummy_shipping_address['state_id'] = State.id
            #     dummy_shipping_address['parent_id'] = partner_sudo.id
            #     _logger.info("Creating dummy shipping address with values: %s", dummy_shipping_address)
            #     request.env['res.partner'].sudo().with_context(
            #         create_context
            #     ).create(dummy_shipping_address)

            
        elif not self._are_same_addresses(address_values, partner_sudo):
            partner_sudo.write(address_values)  # Keep the same partner if nothing changed.

        partner_fnames = set()
        if is_main_address:  # Main address updated.
            partner_fnames.add('partner_id')  # Force the re-computation of partner-based fields.

        if address_type == 'billing':
            partner_fnames.add('partner_invoice_id')
            if is_new_address and order_sudo.only_services:
                # The delivery address is required to make the order.
                partner_fnames.add('partner_shipping_id')
            callback = callback or self._get_extra_billing_info_route(order_sudo)
        elif address_type == 'delivery':
            partner_fnames.add('partner_shipping_id')
            if use_delivery_as_billing:
                partner_fnames.add('partner_invoice_id')

        order_sudo._update_address(partner_sudo.id, partner_fnames)

        if is_anonymous_cart:
            # Unsubscribe the public partner if the cart was previously anonymous.
            order_sudo.message_unsubscribe(order_sudo.website_id.partner_id.ids)

        if is_new_address or order_sudo.only_services:
            callback = callback or '/shop/checkout?try_skip_step=true'
        else:
            callback = callback or '/shop/checkout'

        self._handle_extra_form_data(extra_form_data, address_values)

        return json.dumps({
            'redirectUrl': callback,
        })

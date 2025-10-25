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
            return json.dumps({'redirectUrl': redirection.location})

        partner_sudo, address_type = self._prepare_address_update(
            order_sudo, partner_id=partner_id and int(partner_id), address_type=address_type
        )
        use_delivery_as_billing = str2bool(use_delivery_as_billing or 'false')
        required_fields = required_fields or ''

        # Parse form data into address values, and extract incompatible data as extra form data.
        address_values, extra_form_data = self._parse_form_data(form_data)

        is_anonymous_cart = order_sudo._is_anonymous_cart()
        is_main_address = is_anonymous_cart or order_sudo.partner_id.id == partner_sudo.id
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

import odoo.tests

from odoo import api
from odoo.addons.website_sale.tests.test_sale_process import TestWebsiteSaleCheckoutAddress
from odoo.addons.website.tools import MockRequest
from ..controllers.main import WebsiteSaleExtend


@odoo.tests.tagged('post_install', '-at_install', 'website_sale_address')
class TestWebsiteSaleAddressChange(TestWebsiteSaleCheckoutAddress):
    # Run tests on a clean database with demo data

    def setUp(self):
        super(TestWebsiteSaleAddressChange, self).setUp()
        self.WebsiteSaleController = WebsiteSaleExtend()
        self.website = self.env.ref('website.default_website')

    def test_09_step_by_step_address_field_activation(self):
        """ This test ensure that after hiding the billing/shipping
            address fields there are no errors on address values checks.

            mode "new / billing":
                order.partner_id = public_user.partner_id
                kw['partner_id'] = -1
            mode "edit / billing":
                order.partner_id != public_user.partner_id
                kw['partner_id'] > 0 AND kw['partner_id'] = order.partner_id.id
            mode "new / shipping":
                order.partner_id != public_user.partner_id
                kw['partner_id'] = -1
            mode "edit / shipping":
                kw['partner_id'] > 0 AND kw['partner_id'] != order.partner_id.id
        """
        so = self._create_so(self.website.user_id.partner_id.id)
        env = api.Environment(self.env.cr, self.website.user_id.id, {})
        with MockRequest(
                env, website=self.website.with_env(env), sale_order_id=so.id,
        ) as req:

            req.httprequest.method = "POST"
            mode_list = [
                ('new', 'billing'),
                ('edit', 'billing'),
                ('new', 'shipping'),
                ('edit', 'shipping'),
            ]
            field_list = ['phone', 'street', 'street2', 'city', 'zip', 'state_id']

            for mode in mode_list:
                # Hide all fields
                self.website.write({
                    'use_%s_address_phone' % mode[1]: False,
                    '%s_address_phone_required' % mode[1]: False,
                    'use_%s_address_street' % mode[1]: False,
                    '%s_address_street_required' % mode[1]: False,
                    'use_%s_address_street2' % mode[1]: False,
                    '%s_address_street2_required' % mode[1]: False,
                    'use_%s_address_city' % mode[1]: False,
                    '%s_address_city_required' % mode[1]: False,
                    'use_%s_address_zip' % mode[1]: False,
                    '%s_address_zip_required' % mode[1]: False,
                    'use_%s_address_state' % mode[1]: False,
                    '%s_address_state_required' % mode[1]: False,
                    'use_%s_address_country' % mode[1]: False,
                })
                kw = {
                    'partner_id': -1 if mode[0] == 'new'
                    else self._get_last_address(so.partner_id).id
                    if mode == ('edit', 'shipping') else so.partner_id.id,
                    'name': '%s address (%s)' % (mode[1], mode[0]),
                    'email': 'email@email.email',
                    'country_id': self.env.ref('base.ca').id,
                    'submitted': 1,
                }

                for field in field_list:
                    # Show a field (not required)
                    self.website.write({
                        'use_%s_address_%s' % (
                            mode[1], field.replace('_id', '')): True,
                    })
                    # Check
                    pre_values = self.WebsiteSaleController.values_preprocess(kw)
                    # PATCH: public user can't get a new partner name,
                    # to skip the check "prevent name change if invoices exist"
                    # we remove the partner_id from pre_values
                    without_partner_id_pre_values = pre_values
                    if 'partner_id' in without_partner_id_pre_values:
                        del without_partner_id_pre_values['partner_id']
                    # pylint: disable-msg=unused-variable
                    errors, error_msg = self.WebsiteSaleController.checkout_form_validate(
                        mode, kw, without_partner_id_pre_values,
                    )
                    self.assertFalse(
                        errors, 'The field "%s" value is not set, so there is no error messages.' % field,
                    )

                    # Set as required
                    self.website.write({'%s_address_%s_required' % (mode[1], field.replace('_id', '')): True})
                    # Check
                    pre_values = self.WebsiteSaleController.values_preprocess(kw)
                    without_partner_id_pre_values = pre_values
                    if 'partner_id' in without_partner_id_pre_values:
                        del without_partner_id_pre_values['partner_id']
                    errors, error_msg = self.WebsiteSaleController.checkout_form_validate(
                        mode, kw, without_partner_id_pre_values
                    )
                    self.assertEqual(
                        errors,
                        {field: 'missing'},
                        'The field "%s" value is not set but it is required, so there is an error message.' % field,
                    )

                    # Set a value
                    if '_id' not in field:
                        kw[field] = 'Value'
                    elif field == 'state_id':
                        kw[field] = self.env.ref('base.state_ca_ab').id
                    elif field == 'country_id':
                        kw[field] = self.env.ref('base.ca').id
                    # Check
                    pre_values = self.WebsiteSaleController.values_preprocess(kw)
                    without_partner_id_pre_values = pre_values
                    if 'partner_id' in without_partner_id_pre_values:
                        del without_partner_id_pre_values['partner_id']
                    errors, error_msg = self.WebsiteSaleController.checkout_form_validate(
                        mode, kw, without_partner_id_pre_values,
                    )
                    self.assertFalse(
                        errors,
                        'The field "%s" value is required and it is set, so there are no error messages.' % field,
                    )

                self.WebsiteSaleController.address(**kw)

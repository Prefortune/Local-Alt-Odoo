# Copyright © 2020 Garazd Creation (<https://garazd.biz>)
# @author: Yurii Razumovskyi (<support@garazd.biz>)
# @author: Iryna Razumovska (<support@garazd.biz>)
# License OPL-1 (https://www.odoo.com/documentation/14.0/legal/licenses.html#odoo-apps).

from odoo import _, api, fields, models


class Website(models.Model):
    _inherit = "website"

    # Billing Address fields
    use_billing_address_phone = fields.Boolean(
        string='Phone',
        default=True,
    )
    billing_address_phone_required = fields.Boolean(
        string='Phone is required',
        help='Set the Phone as a required field',
        default=False,
    )
    use_billing_address_street = fields.Boolean(
        string='Street',
        default=True,
    )
    billing_address_street_required = fields.Boolean(
        string='Street is required',
        help='Set the Street as a required field',
        default=True,
    )
    use_billing_address_street2 = fields.Boolean(
        string='Street 2',
        default=True,
    )
    billing_address_street2_required = fields.Boolean(
        string='Street 2 is required',
        help='Set the Street 2 as a required field',
    )
    use_billing_address_city = fields.Boolean(
        string='City',
        default=True,
    )
    billing_address_city_required = fields.Boolean(
        string='City is required',
        help='Set the City as a required field',
        default=True,
    )
    use_billing_address_zip = fields.Boolean(
        string='Zip Code',
        default=True,
    )
    billing_address_zip_required = fields.Boolean(
        related='default_billing_country_id.zip_required',
        string='Zip Code is required',
        help='Set the Zip Code as a required field',
        readonly=False,
    )
    use_billing_address_state = fields.Boolean(
        string='State',
        default=True,
    )
    billing_address_state_required = fields.Boolean(
        related='default_billing_country_id.state_required',
        string='State is required',
        help='Set the State as a required field',
        readonly=False,
    )
    use_billing_address_country = fields.Boolean(
        string='Country',
        default=True,
    )
    default_billing_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Default Country',
    )
    default_billing_country_only = fields.Boolean(
        string='Country is not changeable',
        help='Disable to change the Country',
        default=True,
    )

    # Shipping Address fields
    use_shipping_address_phone = fields.Boolean(
        string='Shipping Phone',
        default=True,
    )
    shipping_address_phone_required = fields.Boolean(
        string='Shipping phone is required',
        help='Set the Phone as a required field',
        default=False,
    )
    use_shipping_address_street = fields.Boolean(
        string='Shipping Street',
        default=True,
    )
    shipping_address_street_required = fields.Boolean(
        string='Shipping Street is required',
        help='Set the Street as a required field',
        default=True,
    )
    use_shipping_address_street2 = fields.Boolean(
        string='Shipping Street 2',
        default=True,
    )
    shipping_address_street2_required = fields.Boolean(
        string='Shipping Street 2 is required',
        help='Set the Shipping Street 2 as a required field',
    )
    use_shipping_address_city = fields.Boolean(
        string='Shipping City',
        default=True,
    )
    shipping_address_city_required = fields.Boolean(
        string='ShippingCity is required',
        help='Set the Shipping City as a required field',
        default=True,
    )
    use_shipping_address_zip = fields.Boolean(
        string='Shipping Zip Code',
        default=True,
    )
    shipping_address_zip_required = fields.Boolean(
        related='default_shipping_country_id.zip_required',
        string='Shipping Zip Code is required',
        help='Set the Shipping Zip Code as a required field',
        readonly=False,
    )
    use_shipping_address_state = fields.Boolean(
        string='Shipping State',
        default=True,
    )
    shipping_address_state_required = fields.Boolean(
        related='default_shipping_country_id.state_required',
        string='Shipping State is required',
        help='Set the Shipping State as a required field',
        readonly=False,
    )
    use_shipping_address_country = fields.Boolean(
        string='Shipping Country',
        default=True,
    )
    default_shipping_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Default Shipping Country',
    )
    default_shipping_country_only = fields.Boolean(
        string='Shipping Country is not changeable',
        help='Disable to change the Country',
        default=True,
    )

    @api.onchange('default_billing_country_only', 'default_billing_country_id')
    def _onchange_default_billing_country_only(self):
        for website in self:
            if not website.default_billing_country_only or not website.default_billing_country_id:
                website.use_billing_address_zip = True
                website.use_billing_address_state = True
                website.use_billing_address_country = True

    @api.onchange('billing_address_zip_required')
    def _onchange_billing_address_zip_required(self):
        if self.default_billing_country_id:
            return {'warning': {
                'title': "Warning",
                'message': _(
                    'By setting this field you change the field "Zip Required" of the country "%s".',
                    self.default_billing_country_id.name,
                ),
                'type': 'notification',
            }}
        return {}

    @api.onchange('use_billing_address_zip')
    def _onchange_use_billing_address_zip(self):
        for website in self:
            if website.billing_address_zip_required:
                website.use_billing_address_zip = True
                return {'warning': {
                    'title': "Warning",
                    'message': _("You can't deactivate this field as it is required for the default country."),
                    'type': 'notification',
                }}
            return {}

    @api.onchange('billing_address_state_required')
    def _onchange_billing_address_state_required(self):
        if self.default_billing_country_id:
            return {'warning': {
                'title': "Warning",
                'message': _(
                    'By setting this field you change the field "State Required" of the country "%s".',
                    self.default_billing_country_id.name,
                ),
                'type': 'notification',
            }}
        return {}

    @api.onchange('use_billing_address_state')
    def _onchange_use_billing_address_state(self):
        for website in self:
            if website.billing_address_state_required:
                website.use_billing_address_state = True
                return {'warning': {
                    'title': "Warning",
                    'message': _("You can't deactivate this field as it is required for the default country."),
                    'type': 'notification',
                }}
            return {}

    @api.onchange('use_billing_address_street', 'use_billing_address_street2')
    def _onchange_use_billing_address_street(self):
        for website in self:
            if not website.use_billing_address_street:
                website.use_billing_address_street2 = False

    @api.onchange('default_shipping_country_only', 'default_shipping_country_id')
    def _onchange_default_shipping_country_only(self):
        for website in self:
            if not website.default_shipping_country_only or not website.default_shipping_country_id:
                website.use_shipping_address_zip = True
                website.use_shipping_address_state = True
                website.use_shipping_address_country = True

    @api.onchange('shipping_address_zip_required')
    def _onchange_shipping_address_zip_required(self):
        if self.default_shipping_country_id:
            return {'warning': {
                'title': "Warning",
                'message': _(
                    'By setting this field you change the field "Zip Required" of the country "%s".',
                    self.default_shipping_country_id.name,
                ),
                'type': 'notification',
            }}
        return {}

    @api.onchange('use_shipping_address_zip')
    def _onchange_use_shipping_address_zip(self):
        for website in self:
            if website.shipping_address_zip_required:
                website.use_shipping_address_zip = True
                return {'warning': {
                    'title': "Warning",
                    'message': "You can't deactivate this field as it is required for the default country.",
                    'type': 'notification',
                }}
            return {}

    @api.onchange('shipping_address_state_required')
    def _onchange_shipping_address_state_required(self):
        if self.default_shipping_country_id:
            return {'warning': {
                'title': "Warning",
                'message': _(
                    'By setting this field you change the field "State Required" of the country "%s".',
                    self.default_shipping_country_id.name,
                ),
                'type': 'notification',
            }}
        return {}

    @api.onchange('use_shipping_address_state')
    def _onchange_use_shipping_address_state(self):
        for website in self:
            if website.shipping_address_state_required:
                website.use_shipping_address_state = True
                return {'warning': {
                    'title': "Warning",
                    'message': _("You can't deactivate this field as it is required for the default country."),
                    'type': 'notification',
                }}
            return {}

    @api.onchange('use_shipping_address_street', 'use_shipping_address_street2')
    def _onchange_use_shipping_address_street(self):
        for website in self:
            if not website.use_shipping_address_street:
                website.use_shipping_address_street2 = False

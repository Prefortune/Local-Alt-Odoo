from odoo import fields, models


class ComponentsInherit(models.Model):
    _inherit = "components"

    interactive_type = fields.Selection(
        selection_add=[
            ("order_details", "ORDER DETAILS"),
            ("catalog_message", "Catalog Message"),
        ]
    )


class WaButtonComponent(models.Model):
    _inherit = 'wa.button.component'

    button_type = fields.Selection(selection_add=[("CATALOG", "Catalogue")])
    product_retailer_id = fields.Char(string="Product Retailer ID")

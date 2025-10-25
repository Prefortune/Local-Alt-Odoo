# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    alt_print_image = fields.Boolean(
        string="Print Image",
        default=True,
        store=True,
        help="If ticked, you can see the product image in report of sale order/quotation"
    )
    alt_image_sizes = fields.Selection(
        selection=[
            ("image", "Big sized Image"),
            ("image_medium", "Medium Sized Image"),
            ("image_small", "Small Sized Image"),
        ],
        string="Image Sizes",
        default="image_small",
        store=True,
        help="Image size to be displayed in report"
    )
    alt_hide_summary_in_quote = fields.Boolean(
        string="Hide Summary in Quote",
        default=False,
        store=True,
        help="If ticked, the price summary table will be hidden in quotations (not applicable for confirmed orders)"
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    alt_image_small = fields.Binary(
        string="Product Image",
        related="product_id.image_1920",
        store=False
    )

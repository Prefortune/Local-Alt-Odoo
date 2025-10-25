# See LICENSE file for full copyright and licensing details.

{
    # Module information
    "name": "alt_product_image_for_sale",
    "version": "18.0.1.0.0",
    "category": "Sales Management",
    "sequence": "1",
    "summary": """Alt Product Image for Quotation/Sale Reports.""",
    "description": """Alt Product Image for Quotation/Sale Reports.""",
    "license": "LGPL-3",
    # Author
    "author": "Alt Mobile Studio",
    "website": "https://altmobilestudio.com",
    "maintainer": "Alt Mobile Studio",
    # Dependencies
    "depends": ["sale_management","alt_split_delivery"],
    # Views
    "data": [
        "views/alt_sale_product_view.xml", 
        "views/alt_report_saleorder.xml",
        "views/alt_sale_order_action.xml",
        "views/alt_report_pick_order.xml",
        "views/alt_report_greeting_card.xml",
        "views/alt_report_picking_card.xml"

    ],
    'assets': {
        'web.report_assets_common': [
            # 'alt_product_image_for_sale/static/src/css/style.css',
            ],
    },
    # Odoo App Store Specific
    "images": ["static/description/alt_banner.png"],
    # Techical
    "installable": True,
    "auto_install": False,
}

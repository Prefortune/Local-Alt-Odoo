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
    "depends": ["sale_management"],
    # Views
    "data": ["views/alt_sale_product_view.xml", "views/alt_report_saleorder.xml"],
    # Odoo App Store Specific
    "images": ["static/description/alt_banner.png"],
    # Techical
    "installable": True,
    "auto_install": False,
}

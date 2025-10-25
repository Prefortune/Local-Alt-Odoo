# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Import Product Images From Zip For E-Commerce",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "eCommerce",
    "summary": "import ecommerce pictures update ecommerce images import image from zip shop import product image from zip import bulk image from zip import partner image from zip product image Import Product Images using product internal reference Odoo",
    "description": """This module will help you to import the bulk of eCommerce images from a zip file. You can import images by name, reference, barcode & ID. You can export extra product images for eCommerce. You just need to manage all image files in one zip and need to select that zip and import it, it will auto-update all images.""",
    "version": "0.0.1",
    "depends": [
        "sh_message",
        "website_sale",
    ],
    "application": True,
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "wizard/import_img_zip_wizard_views.xml",
        "views/sale_views.xml",
    ],
    "images": ["static/description/background.png", ],
    "license": "OPL-1",
    "auto_install": False,
    "installable": True,
    "price": 16,
    "currency": "EUR"
}

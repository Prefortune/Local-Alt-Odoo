# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name":
    "Import Product Variant Special For E-Commerce From CSV | Import Product Variant Special For E-Commerce From Excel",
    "author":
    "Softhealer Technologies",
    "website":
    "https://www.softhealer.com",
    "support":
    "support@softhealer.com",
    "category":
    "Productivity",
    "summary":
    "Import Product Variant From CSV,  Import ecommerce Product Variant Excel App,Import ecommerece Product Variant XLS, Import  Product Variant From XLSX Moule, Product Variant From Excel Odoo",
    "description":
    """This module helps to import the product variant eCommerce category from CSV/Excel file.""",
    "version":
    "0.0.1",
    "depends":
    ["sh_message", "sale_management", "stock", "account", "website_sale"],
    "application":
    True,
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "wizard/import_wizard.xml",
        "views/sale_view.xml",
    ],
    "external_dependencies": {
        "python": ["xlrd"],
    },
    "images": [
        "static/description/background.png",
    ],
    "auto_install":
    False,
    "license":
    "OPL-1",
    "installable":
    True,
    "price":
    32,
    "currency":
    "EUR"
}

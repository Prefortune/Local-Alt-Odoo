# -*- coding: utf-8 -*-

{
    "name": "Bizzup Price Access Customization",
    "summary": """This module allows to restrict the price and product based 
    on the company""",
    "description": """Bizzup Price Access Customization""",
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "category": "POS/Payment",
    "version": "18.0.1.6.4",
    "depends": [
        "sale_management",
        "account",
        "point_of_sale",
    ],
    "data": [
        "security/price_access_security.xml",
        "views/res_company_views.xml",
        "views/sale_order_views.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
        "views/account_move_views.xml",
        "views/purchase_order_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "bizzup_price_access_customization/static/src/**/*",
        ],
    },
    "installable": True,
}

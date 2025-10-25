# -*- coding: utf-8 -*-
# Part of Creyox Technologies
{
    "name": "Filter Delivery Record",
    "author": "Creyox Technologies",
    "website": "https://www.creyox.com",
    "support": "support@creyox.com",
    "version": "18.0",
    "summary":
        """
        """,
    "sequence": 10,
    "description":
        """
        """,
    "category": "stock",
    "price": '',
    "currency": "USD",
    "license": "OPL-1",
    "depends": ["base", "stock"],
    "data": [
    'views/stock_picking.xml',
    ],
    'post_init_hook': '_post_init_hook',
    "installable": True,
    "auto_install": False,
    "application": True,
    "images": ["static/description/banner.png"],
}

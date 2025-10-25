# -*- coding: utf-8 -*-

{
    "name": "Bizzup Contact Customization",
    "description": """
        Ticket : HT01264 | (Add new fields to contact - Matzman).""",
    "version": "18.0.1.0.0",
    "category": "Contacts",
    "license": "Other proprietary",
    "author": "Lilach Gillam",
    "website": "www.bizzup.app",
    "depends": ["contacts", "stock", "sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_form_view.xml",
        "views/delivery_route_view.xml",
        "views/stock_picking_view.xml",
        "views/sale_order_view.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
}

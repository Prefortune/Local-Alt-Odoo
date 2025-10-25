# -*- coding: utf-8 -*-

{
    "name": "Bizzup Report Internal Ref",
    "description": """
        Ticket : HT01262 | (Make some changes in some reports - Matzman)

Use cases:

1) Add to the following reports a column for the internal ref of the product
        a) RFQ, Sale order, delivery slip, Invoice
        b) If the internal ref is not set, so the cell will stay empty
        c) Add this also in the portal reports
""",
    "version": "18.0.1.0.2",
    "category": "Contacts",
    "license": "Other proprietary",
    "author": "Lilach Gillam",
    "website": "www.bizup.app",
    "depends": [
        "sale_management",
        "purchase",
        "account_accountant",
        "stock",
    ],
    "data": [
        'report/delivery_slip_report_views.xml',
        'report/invoice_report_views.xml',
        'report/purchase_order_report_views.xml',
        'report/sale_order_report_views.xml',
        'report/product_template_views.xml',
    ],
    "demo": [],
    "installable": True,
    "application": False,
}

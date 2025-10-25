# -*- coding: utf-8 -*-

{
    "name": "Bizzup Tranzila POS Connect",
    "summary": """This module allows to make a Payment from Tranzila POS
    Pyhsical Terminal""",
    "description": """Payment Tranzila POS Machine Terminal
        When Order is confirmed from POS Machine and when user close
        the session the journal entry of the current order will be 
        matched, and if the current order's partner does not have a vat
        and amount is gretater than the limit set for vat in acoutning setting
        then validation pop-up for vat requires will come for any payment method
        Ticket - HT01506""",
    "license": "Other proprietary",
    "author": "Lilach Gilliam",
    "website": "https://bizzup.app",
    "category": "POS/Payment",
    "version": "18.0.1.7.2",
    "depends": [
        "point_of_sale",
        "pos_online_payment",
        "payment",
        "bizzup_tranzila_pos_machine",
        "bizzup_margin_limit",
    ],
    "data": [
        "views/pos_payment_method_views.xml",
        "data/pos_tranzila_connect_data.xml",
        "views/pos_session_views.xml",
        "views/pos_order_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "bizzup_pos_tranzila_connect/static/src/**/*",
        ],
    },
    "installable": True,
    "post_init_hook": "post_init",
}

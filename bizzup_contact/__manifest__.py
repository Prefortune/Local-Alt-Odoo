# -*- coding: utf-8 -*-
{
    "name": "Bizzup Contact",
    "description": """
        US HT01267 : 
        Display the customer statment as a field - Matzman.
    """,
    "version": '18.0.1.0.0',
    "license": 'Other proprietary',
    "author": 'Lilach Gilliam',
    "website": 'https://bizzup.app',
    "depends": ['account_followup', 'pos_settle_due', 'point_of_sale'],
    "data": [
        "views/res_partner_views.xml",
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'bizzup_contact/static/src/**/*',
        ],
    },
    "application": True,
    "installable": True,
}


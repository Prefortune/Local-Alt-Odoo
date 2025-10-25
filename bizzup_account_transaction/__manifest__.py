# -*- coding: utf-8 -*-

{
    "name": "Bizzup Account Transaction",
    "description": """
        Ticket : HT01585 | (Make changes in Accounting - MM).""",
    "version": "18.0.2.0.0",
    "category": "Accounting",
    "license": "Other proprietary",
    "author": "Lilach Gillam",
    "website": "www.bizzup.app",
    "depends": ["account", "base", 'bizzup_tranzila_receipt_updates'],
    "data": [
        'views/account_move_views.xml',
        'views/account_journal_dashboard_view.xml',
    ],
    "demo": [],
    "installable": True,
    "application": False,
}

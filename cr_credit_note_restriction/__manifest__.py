# -*- coding: utf-8 -*-
# Part of Creyox Technologies
{
    "name": "Credit Note Restriction",
    "author": "Creyox Technologies",
    "website": "https://www.creyox.com",
    "support": "support@creyox.com",
    "category": "Extra Tools",
    "summary": "This module enhances financial control and refund validation in Odoo. It restricts credit note creation to only via Sales Orders and Invoices, and prevents posting of credit notes by regular users—only Accounting Managers can post them. It also disables converting regular invoices into credit notes. Additionally, in the Point of Sale (POS) interface, non-manager employees are required to enter a valid manager PIN before processing a refund, ensuring secure and authorized refund handling.",
    "license": "LGPL-3",
    "version": "18.0",
    "description": """ 
        """,
    "depends": [
        "base",
        "web",
        "point_of_sale",
        'sale_management'
        ,'account',
    ],
    "data": [
    ],
    'assets': {
        'point_of_sale._assets_pos': [
                'cr_credit_note_restriction/static/src/**/*'
            ],
        },
    "installable": True,
    "auto_install": False,
    "application": True,
}

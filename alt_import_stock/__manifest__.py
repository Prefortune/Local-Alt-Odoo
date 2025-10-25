# -*- coding: utf-8 -*-
# Part of alt AV ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Alt Import Stock',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Import stock data from Excel files',
    'description': """
        This module provides functionality to import stock data from Excel files.
        Features:
        - Import quantities from Excel files
        - Support for Excel format
    """,
    'author': 'Alt Mobile Studio',
    'website': 'https://www.altmobilestudio.com',
    'depends': [
        'base',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/import_stock_move_file_view.xml',
        'views/stock_picking_form_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'live_test_url': 'https://youtu.be/0bdHmEPALRs',
    "images": ['static/description/Banner.png'],
    'license': 'OPL-1',
}

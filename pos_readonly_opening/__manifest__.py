{
    'name': 'POS Readonly Opening Cash',
    'version': '18.0',
    'category': 'Point of Sale',
    'summary': 'Readonly POS cash opening, pos cash opening restrict pos disable cash opening pos cash control restrict pos access cash opening pos access pos opening access pos access pos security pos cash control access.',
    'description': """This module modifies the Cash Opening Popup in Odoo POS to make the Opening Cash field read-only.""",
    'author': 'Khaled Hassan',
    'website': "https://apps.odoo.com/apps/modules/browse?search=Khaled+hassan",
    'depends': ['point_of_sale'],
    'application': False,
    'currency': 'EUR',
    'price': '10',
    'license': 'OPL-1',
    'installable': True,
    'data': [
    ],
    'images': [
        'static/description/banner.png',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_readonly_opening/static/src/**/*'
        ],
    },
}

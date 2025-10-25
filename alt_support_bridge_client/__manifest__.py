{
    'name': 'Alt Support Bridge Client',
    'version': '1.0',
    'category': 'Discuss',
    'summary': 'Client module for Alt Support Bridge',
    'description': """
        This module enables clients to communicate with the central support system
        through their Odoo Discuss channels.
    """,
    'author': 'AltAVltd',
    'website': 'https://altavltd.com',
    'depends': [
        'mail',
        'base',
        'base_setup',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/mail_channel_views.xml',
        'views/res_config_settings_views.xml',
        'views/alt_support_config_views.xml',
        'menus/alt_support_menu.xml',
        'data/personal_channel.xml',
        'data/shared_channel.xml',
        'data/alt_support_config.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 
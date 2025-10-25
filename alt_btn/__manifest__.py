{
    'name': 'alt Button',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Adds a sticky container in footer',
    'description': """
        This module adds a sticky container with text before the footer.
    """,
    'author': 'alt A/V',
    'website': 'https://www.altavltd.com',
    'depends': ['website'],
    'data': [
        'views/sticky_button_config_views.xml',
        'views/menu.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'alt_btn/static/src/scss/style.scss',
            'alt_btn/static/src/xml/template.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
} 
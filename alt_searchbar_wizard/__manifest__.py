{
    'name': 'Alt Searchbar Wizard',
    'version': '18.0.2.0.0',
    'category': 'Website',
    'summary': 'Dynamic configurable searchbar for websites',
    'description': """
        This module adds a dynamic, configurable searchbar component that can be used on any website page.
        Each website can define its own searchbar structure and filters using a backend configuration model.
        
        Features:
        - Dynamic searchbar with configurable fields
        - Support for categories, attributes, and price filters
        - Bootstrap 5 styling with theme support
        - Multi-website support
        - SEO optimized URLs
    """,
    'author': 'Alt Mobile Studio',
    'website': 'https://www.altmobilestudio.com',
    'depends': [
        'base',
        'website',
        'website_sale',
        'product',
    ],
    'data': [
        'security/alt_searchbar_security.xml',
        'security/ir.model.access.csv',
        'data/alt_searchbar_data.xml',
        'views/alt_searchbar_views.xml',
        'views/alt_searchbar_templates.xml',
    ],
    'assets': {
        'web.assets_common': [
            'alt_searchbar_wizard/static/src/js/searchbar_loader.js',
        ],
        'web.assets_frontend': [
            'alt_searchbar_wizard/static/src/css/style.css',
            'alt_searchbar_wizard/static/src/js/searchbar_loader.js',
            'alt_searchbar_wizard/static/src/js/wizard_button.js',
        ],
        'web.assets_frontend_minimal': [
            'alt_searchbar_wizard/static/src/js/searchbar_loader.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'],
} 
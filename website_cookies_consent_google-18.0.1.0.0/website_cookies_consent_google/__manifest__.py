# Copyright © 2024 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/master/legal/licenses.html#odoo-apps).

{
    'name': 'Odoo Google Consent Mode',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'author': 'Garazd Creation',
    'website': 'https://garazd.biz/shop',
    'license': 'OPL-1',
    'summary': 'Odoo Google Consent Mode | Google consent mode v2 | Google Consent Management',
    'images': ['static/description/banner.png', 'static/description/icon.png'],
    'live_test_url': 'https://garazd.biz/r/kud',
    'depends': [
        'website_google_analytics_4',
        'website_cookies_consent',
        'website_google_tag',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/website_templates.xml',
        'views/website_views.xml',
        'views/website_google_consent_views.xml',
        'views/website_google_consent_region_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'data/website_demo.xml',
        'data/website_google_consent_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_cookies_consent_google/static/src/js/cookies_bar.js',
        ],
    },
    'price': 34.00,
    'currency': 'EUR',
    'support': 'support@garazd.biz',
    'application': True,
    'installable': True,
    'auto_install': False,
}

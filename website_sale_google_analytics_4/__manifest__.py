# Copyright © 2021 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/master/legal/licenses.html#odoo-apps).

# flake8: noqa: E501

{
    'name': 'Odoo Google Analytics 4 eCommerce Tracking',
    'version': '18.0.1.2.0',
    'category': 'eCommerce',
    'author': 'Garazd Creation',
    'website': 'https://garazd.biz/shop',
    'license': 'OPL-1',
    'summary': 'Google Analytics 4 for eCommerce | GA4 Retail and Ecommerce Events',
    'images': ['static/description/banner.png', 'static/description/icon.png'],
    'live_test_url': 'https://garazd.biz/r/ZUu',
    'depends': [
        'website_sale_tracking_base',
        'website_cookies_consent_google',
    ],
    'data': [
        'data/res_users_data.xml',
        'views/website_templates.xml',
        'views/res_users_views.xml',
        'views/website_tracking_service_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'data/website_tracking_service_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_sale_google_analytics_4/static/src/js/website_sale_tracking.js',
            'website_sale_google_analytics_4/static/src/js/website_sale_tracking_ga4.js',
        ],
    },
    'price': 94.00,
    'currency': 'EUR',
    'support': 'support@garazd.biz',
    'application': True,
    'installable': True,
    'auto_install': False,
}

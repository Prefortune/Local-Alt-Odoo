# Copyright © 2024 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/master/legal/licenses.html#odoo-apps).

{
    'name': 'Odoo Google Tag Manager Enhanced Conversion Tracking',
    'version': '18.0.1.0.0',
    'category': 'eCommerce',
    'author': 'Garazd Creation',
    'website': 'https://garazd.biz/en/shop/odoo-gtm-conversion-194',
    'license': 'OPL-1',
    'summary': 'Google Tag Manager Conversions | GTM Enhanced Conversions',
    'images': ['static/description/banner.png', 'static/description/icon.png'],
    'live_test_url': 'https://garazd.biz/r/y2O',
    'depends': [
        'website_sale_google_analytics_4',
    ],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'data/website_tracking_service_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_sale_google_tag/static/src/js/website_sale_tracking_gtm.js',
        ],
    },
    'price': 45.00,
    'currency': 'EUR',
    'support': 'support@garazd.biz',
    'application': True,
    'installable': True,
    'auto_install': False,
}

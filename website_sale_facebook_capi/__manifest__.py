# Copyright © 2023 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/master/legal/licenses.html#odoo-apps).

# flake8: noqa: E501

{
    'name': 'Odoo Facebook Conversions API | Meta Conversion API Integration',
    'version': '18.0.1.1.0',
    'category': 'eCommerce',
    'author': 'Garazd Creation',
    'website': 'https://garazd.biz/odoo-website-tracking',
    'license': 'OPL-1',
    'summary': 'Meta Facebook Conversions API | Facebook Conversion API | Meta CAPI for Tracking Events | Facebook CAPI Integration',
    'images': ['static/description/banner.gif', 'static/description/icon.png'],
    'live_test_url': 'https://garazd.biz/r/pMe',
    'depends': [
        'website_sale_facebook_pixel',
    ],
    'data': [
        'data/ir_cron_data.xml',
        'views/website_tracking_log_views.xml',
    ],
    'demo': [
        'data/website_tracking_service_demo.xml',
    ],
    'price': 118.50,
    'currency': 'EUR',
    'support': 'support@garazd.biz',
    'application': True,
    'installable': True,
    'auto_install': False,
}

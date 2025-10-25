# Copyright © 2020 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/master/legal/licenses.html#odoo-apps).

# flake8: noqa: E501

{
    'name': 'Odoo Facebook Catalog Integration and Instagram Shopping',
    'version': '18.0.1.0.0',
    'category': 'eCommerce',
    'author': 'Garazd Creation',
    'website': 'https://garazd.biz/shop',
    'license': 'OPL-1',
    'summary': 'Advertise and sell products on Facebook Catalogue and Instagram Catalog | Data Feed | Data Import | Data Source | FB Product Catalog | Odoo Instagram Feed',
    'images': ['static/description/banner.png', 'static/description/icon.png'],
    'live_test_url': 'https://garazd.biz/r/aVo',
    'depends': [
        'product_data_feed',
        'product_google_category',
        'product_facebook_category',
        'product_data_feed_brand',
        'product_data_feed_number',
    ],
    'data': [
        'data/product_data_feed_recipient_data.xml',
        'data/product_data_feed_data.xml',
        'data/product_data_feed_column_value_data.xml',
        'data/product_data_feed_column_data.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
    ],
    'demo': [
        'demo/product_demo.xml',
        'demo/product_data_feed_demo.xml',
    ],
    'price': 85.00,
    'currency': 'EUR',
    'support': 'support@garazd.biz',
    'application': True,
    'installable': True,
    'auto_install': False,
}

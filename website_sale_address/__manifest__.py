# Copyright © 2020 Garazd Creation (https://garazd.biz)
# @author: Yurii Razumovskyi (support@garazd.biz)
# @author: Iryna Razumovska (support@garazd.biz)
# License OPL-1 (https://www.odoo.com/documentation/master/legal/licenses.html#odoo-apps).

# flake8: noqa: E501

{
    'name': 'eCommerce Address Management',
    'version': '17.0.1.0.0',
    'category': 'eCommerce',
    'author': 'Garazd Creation',
    'website': 'https://garazd.biz/en/blog/odoo-e-commerce/management-of-the-billing-and-shipping-address-fields-in-odoo-ecommerce-5',
    'license': 'OPL-1',
    'summary': 'eCommerce Billing and Shipping Address Fields | Odoo e-commerce extension | Odoo Express Checkout',
    'images': ['static/description/banner.gif', 'static/description/icon.png'],
    'live_test_url': 'https://garazd.biz/r/qqY',
    'depends': [
        'website_sale',
    ],
    'data': [
        'views/website_views.xml',
        'views/website_sale_templates.xml',
    ],
    'price': 38.71,
    'currency': 'EUR',
    'support': 'support@garazd.biz',
    'application': True,
    'installable': True,
    'auto_install': False,
}

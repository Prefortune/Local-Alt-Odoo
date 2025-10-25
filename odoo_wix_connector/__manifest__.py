# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    'name': 'Wix Odoo Connector | Odoo Multichannel',
    'description':      """
                            Odoo Wix Connector for Multichannel integrates your 
                            Odoo with Wix to make the shopping experience seamless. 
                            The module allows you to sync products, categories, and 
                            orders to Odoo so that you can efficiently manage. Also, 
                            automatically sync data to Odoo using the cron.
                        """,
    'summary':          """
                            Odoo Wix Connectors integrates your Odoo with Wix to make 
                            the shopping experience seamless. The module allows you to 
                            sync products, categories, and sync orders to Odoo so that 
                            you can efficiently manage.
                            Multichannel is also compatible with these webkul apps
                            Amazon Connector Ebay Connector Magento Connector Woocommerce
                            Connector Shopify Connector Shopware Connector Walmart
                            Connector Lazada Connector Prestashop Connector flipkart connector odoo Apps
                            Ecommerce Connectors for wix multi-channel wix ecommerce webkul connectors
                        """,
    'version':  '1.6.3',
    'license':  'Other proprietary',

    # Odoo store specific
    'images': ['static/description/banner.png'],
    'category': 'eCommerce',
    'website': 'https://store.webkul.com/odoo-wix-connector-for-multichannel.html',
    'live_test_url': 'https://odoodemo.webkul.com/?module=odoo_wix_connector',

    # Author
    'author':  'Webkul Software Pvt. Ltd.',
    'maintainer': 'Webkul Software Pvt. Ltd.',

    # Data depends
    'depends': [
        'odoo_multi_channel_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/demo.xml',
        'views/views_wix_config_views.xml',
        'views/inherit_dashboard_view.xml',
        'wizard/inherits.xml',
        'wizard/import_operation.xml',
        'wizard/export_operation.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_wix_connector/static/src/xml/instance_dashboard.xml',
        ],
    },

    # Other Technical
    'sequence': 1,
    'application': True,
    'installable': True,
    'auto_install': False,
    'price': 220,
    'currency': 'USD',
    'external_dependencies':  {'python': ['pyjwt==2.6.0']},
    'pre_init_hook': 'pre_init_check',
}

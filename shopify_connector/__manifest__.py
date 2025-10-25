{
    'name': 'Shopify Connector',
    'version': '1.0.0',
    'category': 'Managment',
    'author': 'Prefortune Technologies',
    'sequence': -100,
    'summary': 'Managment System',
    'description': """""",
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'point_of_sale',
        'pf_pos_multi_currency',
        'loyalty'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/menu.xml',
        'views/connector.xml',
        'views/product.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 'shopify_connector/static/src/components/*/*.js',
            # 'shopify_connector/static/src/components/*/*.xml',
        ],
    },
    'demo': [],
    'application': True,
    'auto_install': False,
}

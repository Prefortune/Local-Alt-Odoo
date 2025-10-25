{
    'name': "Clover POs payment in Odoo",
    'version': '18.0.1.0.0',
    'category': '',
    'sequence': -40000,
    'summary': "",
    'license': 'OPL-1',
    'description': """""",
    'author': "Prefortune Technologies LLP",
    'website': "https://www.prefortune.com/",
    'maintainer': 'Prefortune Technologies LLP',
    "support": "odoo@prefortune.com",
    'currency': 'EUR',
	'price': '',
    'depends': ['base','point_of_sale','mail','payment'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_payment_method_views.xml',
        'views/res_config_setting.xml'
        
    ],
    'demo': [],
    "images": ["static/description/banner.png"],
   "assets": {
        "point_of_sale._assets_pos": [
            "pos_clover/static/**/*",
           
        ],
    },
    'installable' : True,
    'application': True,
    'auto_install' : False,
}
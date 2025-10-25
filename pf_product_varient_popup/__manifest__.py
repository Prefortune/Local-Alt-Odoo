
{
    'name': 'POS Variant Customised',
    'version': '17.0',
    'category': 'General',
	'summary': 'POS Variant Customised',
	'author': '',
    'website': '',
    'description': """""",
    'depends': [        
        'point_of_sale',           
    ],
    'data': [            
    ],
    'assets': {
        'point_of_sale._assets_pos': [     
            "pf_product_varient_popup/static/src/app/**/*",
            "pf_product_varient_popup/static/src/overrides/**/*"
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}

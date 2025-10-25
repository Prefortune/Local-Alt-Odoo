
{
    'name': 'POS Customised',
    'version': '17.0',
    'category': 'General',
	'summary': 'POS Customised',
	'author': '',
    'website': '',
    'description': """""",
    'depends': [        
        'point_of_sale',
        'pos_sale',
        'mrp',
        'stock',
        'sale_management'      
    ],
    'data': [     
        "security/ir.model.access.csv",
        "views/pf_invoice_report.xml",
        "views/pf_order_tag.xml",
        "views/pos_config_views.xml",
        "views/pos_order_views.xml",
        "views/stock_picking_views.xml",
        "views/product_product_views.xml"
    ],
    'assets': {
        'point_of_sale._assets_pos': [                             
            'pf_pos_multi_currency/static/src/js/model.js',                       
            'pf_pos_multi_currency/static/src/js/pf_payment_screen.js',
            'pf_pos_multi_currency/static/src/js/payment_screen.js',
            'pf_pos_multi_currency/static/src/js/ticket_screen.js',
            'pf_pos_multi_currency/static/src/xml/payment_screen.xml'
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}

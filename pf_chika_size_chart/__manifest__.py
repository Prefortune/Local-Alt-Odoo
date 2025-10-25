
{
    'name': 'Chika Size Chart',
    'version': '17.0',
    'category': 'General',
	'summary': 'Chika Size Chart',
	'author': '',
    'website': '',
    'description': """""",
    'depends': [
        'base',       
        'contacts', 
        'point_of_sale', 
        'sale',          
        'sale_management'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/pf_size_chart_views.xml',
        'views/sale_order_line_views.xml',
        'views/pos_order_line_views.xml'                    
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pf_chika_size_chart/static/src/popups/variant_popup/variant_popup.xml',         
            'pf_chika_size_chart/static/src/pf_select_size_chart_view.xml',
            'pf_chika_size_chart/static/src/popups/variant_popup/variant_popup.js',
            'pf_chika_size_chart/static/src/pf_select_size_chart.js'                                        
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}

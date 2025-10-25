{
    'name' : 'pf_alt_website_custom',
    'version' : '17.0.0.1',
    'summary': '',
    'sequence': 1,
    'description': """
    """,
    'category': '',
     "depends": ["product","website_sale","theme_prime",'point_of_sale','website','mail','sh_all_in_one_helpdesk','project'],
    'website': '',
    'data': [
        'security/ir.model.access.csv',
        'views/product_descrption.xml',
        'views/product_review_menu.xml',
        'views/product_template_views.xml',
        'views/project_task.xml',
        "views/project_project_views.xml",
        'views/portal_custom.xml'
        ],
    'demo': [
    ],
     'assets': {
       'web.assets_frontend': [
    #    'pf_alt_website_custom/static/src/snippets/dynamic_snipets.js',
            # 'pf_alt_website_custom/static/src/js/snippet.js',
            # 'pf_alt_website_custom/static/src/xml/snippet_template.xml',
            # 'pf_alt_website_custom/static/src/xml/best_seller_snippet.xml'
        ],
        'web.assets_backend': [
            'pf_alt_website_custom/static/src/js/pf_create_ticket.js',
            'pf_alt_website_custom/static/src/xml/pf_create_ticket_views.xml',
            'pf_alt_website_custom/static/src/js/pf_create_review.js',
            'pf_alt_website_custom/static/src/js/pf_create_ticket_owl.js',
        ]
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
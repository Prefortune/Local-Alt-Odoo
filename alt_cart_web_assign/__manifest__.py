{
    'name': 'ALT Website Form Cart Assignment',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Automatically assign cart to customer when submitting website forms',
    'description': """
        This module extends the website_form functionality to automatically assign
        the current shopping cart to a customer when they submit a res.partner form.
        
        Features:
        - Inherits the /website_form/submit controller
        - Automatically links cart to newly created customer
        - Works with standard website forms
        - No additional UI required
    """,
    'author': 'ALT AV LTD',
    'website': 'https://altavltd.com',
    'depends': [
        'website',
        'auth_signup',
        'marketing_automation',
        'mass_mailing'
    ],
    'data': [
        'views/template.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_frontend': [
            '/alt_cart_web_assign/static/src/js/phone_field.js',
        ],
    },
}

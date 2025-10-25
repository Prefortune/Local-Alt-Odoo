{
    'name': "Event Sponsorship in Odoo",
    'version': '18.0.1.0.0',
    'category': 'Event',
    'sequence': -2200,
    'summary': "Handles sponsorships, Stripe payments, and email notifications.",
    'license': 'OPL-1',
    'description': """ 
        The Event Sponsorship module, developed by Prefortune Technologies LLP, is a robust solution designed to simplify and enhance the management of sponsorships for events within a platform, likely integrated with Odoo.
        Key Features:
        -Sponsorship Configuration
        -Stripe Payment Integration
        -Payment Confirmation
        -Automated Email Notifications""",
    'author': "Prefortune Technologies LLP",
    'website': "https://www.prefortune.com/",
    'maintainer': 'Prefortune Technologies LLP',
    "support": "odoo@prefortune.com",
    'currency': 'EUR',
	'price': '',
    'depends': ['event','website_event','website','mail','base','base_setup'],
    'external_dependencies':{
        'python':['stripe']
        },
   'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/mail_template_sponsor.xml',
        'views/event_sponsorship.xml',
        'views/res_config_settings_views.xml',  
        'views/error_template.xml'
    ],
    'demo': [

    ],
    "images": ["static/description/banner.png"],
    'installable' : True,
    'application': True,
    'auto_install' : False,
}

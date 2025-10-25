{
    'name': "Generate Experience And Relieving Letter ",
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'sequence':10,
    'summary': "Prefortune Technologies LLP has created this module which provides functionality to generate professional Employee Experience and Relieving Letters in PDF format using custom templates directly from Odoo.",
    "license": "OPL-1",
    'description': """
       This module enables the generation of professionally formatted Employee Experience and Relieving Certificates using customizable templates within Odoo. Designed specifically for A4 landscape paper format, it allows HR teams to create polished, print-ready PDF documents that include dynamic content such as employee name, job title, and employment dates. Templates with custom background designs (such as gold-gray or dark blue-white) can be selected through system settings, ensuring flexibility and consistency with company branding. The module leverages Odoo’s QWeb reporting engine to deliver clean, visually appealing certificates ideal for official use.
    """,
    'author': "Prefortune Technologies LLP",
    "website": "https://www.prefortune.com/",
    'maintainer': 'Prefortune Technologies LLP',
    "support": "odoo@prefortune.com",
    "images": ["static/description/banner.png"],
    'depends': ['base','hr','hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'data/certificate_actions.xml',
        'data/paper_format.xml',
        'views/res_config_settings.xml',
        'views/certificate_templates.xml',
        'views/certificate_report.xml',
        'views/certificate_wizard.xml',  
    ],
    'currency': 'EUR',
    'price': '',
    'installable': True,
    'application': True,
    'auto_install' : False,
    'assets': {
        'web.assets_backend': [
            'pf_generate_employee_experience_relieving_letter/static/src/scss/template_preview.scss',
        ],
    },
   
}


    # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Login with WhatsApp | Two Factor (2FA) with WhatsApp | Reset Password with WhatsApp | WhatsApp OTP | WhatsApp Login',
    'version': '1.0',
    'author': 'TechUltra Solutions Private Limited',
    'category': 'Hidden/Tools',
    'live_test_url': 'https://www.techultrasolutions.com/blog/news-2/odoo-whatsapp-integration-a-boon-for-business-communication-25',
    'website': 'www.techultrasolutions.com',
    'price': 99,
    'currency': 'USD',
    'summary': """Enable users to sign up using an OTP sent via WhatsApp, implement two-factor authentication through WhatsApp, and allow password resets using WhatsApp.
        WhatsApp SignUp
        Odoo Meta WhatsApp Graph API
        Odoo V17 Community Edition
        Odoo V17 Community WhatsApp Integration
        V17 Community WhatsApp
        Community WhatsApp
        Community
        WhatsApp Community
        Odoo WhatsApp Community
        Odoo WhatsApp Cloud API
        WhatsApp Cloud API
        WhatsApp Community Edition
    """,
    'description': """
        Enable users to sign up using an OTP sent via WhatsApp, implement two-factor authentication through WhatsApp, and allow password resets using WhatsApp.
        Odoo WhatsApp Integration
        Odoo Meta WhatsApp Graph API
        Odoo V17 Community Edition
        Odoo V17 Community WhatsApp Integration
        V17 Community WhatsApp
        Community WhatsApp
        Community
        WhatsApp Community
        Odoo WhatsApp Community
        Odoo WhatsApp Cloud API
        WhatsApp Cloud API
        WhatsApp Community Edition
    """,
    'depends': ['auth_signup', 'tus_meta_whatsapp_base'],
    'data': [
        "security/ir.model.access.csv",
        "views/res_user_inherit.xml",
        "views/whatsapp_signup_login_templates.xml",
        "views/res_config.xml",
        "wizard/whatsapp_otp_auth_totp_views.xml",
        ],
    'assets': {
        'web.assets_frontend': [
            'whatsapp_login/static/src/lib/utils.js',
            'whatsapp_login/static/src/lib/intelinputmin.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
    'images': ['static/description/tus_banner.gif'],
}

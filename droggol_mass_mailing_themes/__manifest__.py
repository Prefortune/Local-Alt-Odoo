# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present Droggol Infotech Private Limited. (<https://www.droggol.com/>)

{
    'name': 'Mass Mailing Theme (with color picker)',
    'summary': 'Send beautiful with your brand colors. 60+ new mailing snippets. (Mass mailing theme, Mass mailing template, Massmailing theme, Email Template)',
    'description': """
        Send beautiful with your brand colors (with color picker).
        60+ new mailing snippets.
        Mass mailing theme,
        Mass mailing template,
        Custom mass mailing theme,
        Custom mail theme,
        Massmailing theme,
        Responsive mail templates,
        Email Template,
        Email colors,
        Email template colors,
        Custom color email,
        Custom color mass mailing theme,
        Dynamic mail snippets,
        Auto fill mail,
        Auto fill mass mail,
        Products email,
        Products mail,
        Offers email,
        Offers mail,
        Blog email,
        Coupon email,
        Coupon mass mail,
        Coupon mail,
        Blog mail,
        Event email,
        Event mail,
        Blog newsletter mail,
        Blog newsletter email,
        Email Branding,
        Email Branding color,
        Custom Email Branding,
        Custom Email Branding,
        Mass mail custom color,
        Mass mail snippets,
        Mass mail building blocks,
        Email snippets
    """,

    'version': '17.0.0.0.0',
    'license': 'OPL-1',
    'category': 'Marketing',
    'author': 'DROGGOL INFOTECH PRIVATE LIMITED',
    'company': 'DROGGOL INFOTECH PRIVATE LIMITED',
    'maintainer': 'DROGGOL INFOTECH PRIVATE LIMITED',
    'website': 'https://www.droggol.com/',
    'live_test_url': 'https://youtu.be/eUl7LcLpm0s',
    'depends': [
        'mass_mailing',
    ],
    'data': [
        'views/mass_mailing_themes_templates.xml',
        'views/res_config_settings_views.xml',
        'views/s_generic_blocks.xml',
        'views/snippets.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'droggol_mass_mailing_themes/static/src/js/color_field.xml',
            'droggol_mass_mailing_themes/static/src/js/color_field.js',
            'droggol_mass_mailing_themes/static/src/scss/d_color_palette_field.scss',
            'droggol_mass_mailing_themes/static/src/xml/**/*',
        ],
        'mass_mailing.assets_mail_themes': [
            'droggol_mass_mailing_themes/static/src/scss/themes/**/*',
        ],
        'mass_mailing.assets_wysiwyg': [
            'droggol_mass_mailing_themes/static/src/js/snippet.options.js',
        ],
    },

    "price": 153.50,
    "currency": "EUR",
    'images': ['static/description/mass_mail_images/cover.png'],
    'installable': True,
    'application': True
}

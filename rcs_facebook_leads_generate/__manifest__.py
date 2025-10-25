# -*- coding: utf-8 -*-

{
    "name": "CRM Facebook Lead Integration - Facebook Leads Connector",
    "version": "18.0.0.0.1",
    "description": """CRM Facebook Lead Integration - Facebook Leads Connector is a powerful Odoo module that connects your Facebook Lead Ads with Odoo CRM. Facebook Lead Integration for Odoo,Odoo Facebook CRM Connector,Facebook Leads to Odoo CRM,Odoo CRM Facebook Integration App,Sync Facebook Leads with Odoo,Odoo Facebook Marketing Automation,Facebook Lead Ads Odoo Integration,Capture Facebook Leads in Odoo,Social Media CRM Integration,Odoo Lead Generation from Facebook,Facebook Ad Forms CRM Sync,Facebook API Connector for Odoo CRM.
                """,
    "summary": """
        CRM Facebook Lead Integration - Facebook Leads Connector is a powerful Odoo module that connects your Facebook Lead Ads with Odoo CRM. Facebook Lead Integration for Odoo,Odoo Facebook CRM Connector,Facebook Leads to Odoo CRM,Odoo CRM Facebook Integration App,Sync Facebook Leads with Odoo,Odoo Facebook Marketing Automation,Facebook Lead Ads Odoo Integration,Capture Facebook Leads in Odoo,Social Media CRM Integration,Odoo Lead Generation from Facebook,Facebook Ad Forms CRM Sync,Facebook API Connector for Odoo CRM.
                """,
    "author": "Reliution",
    "website": "https://www.reliution.com",
    "license": 'AGPL-3',
    "category": "CRM",
    "depends": ['base', 'utm', 'crm', 'web'],
    "data": [
        'data/facebook.form.mapping.csv',
        'data/facebook_lead_data.xml',
        'data/ir_cron.xml',

        'security/facebook_leads_security.xml',
        'security/ir.model.access.csv',

        'views/facebook_app_credential_views.xml',
        'views/facebook_form_mapping_views.xml',
        'views/facebook_form_views.xml',
        'views/facebook_page_views.xml',
        'views/crm_lead_views.xml',
        'views/crm_team_views.xml',
        'views/facebook_page_category.xml',
        'views/facebook_leads_menu_views.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "rcs_facebook_leads_generate/static/src/js/list_view_patch.js",
        ],
    },
    "images": ['static/description/banner.gif'],
    'price': 30.00,
    'currency': 'USD',
    "installable": True,
    "application": True,
    'auto_install': False,
}

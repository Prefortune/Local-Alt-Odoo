{
    'name': 'Alt Support Bridge Server',
    'version': '18.0.1.0.0',
    'category': 'Services/Support',
    'summary': 'Server module for Alt Support Bridge',
    'description': """
        This module enables the central support system to communicate with client instances
        through a secure API token-based system.
        
        Features:
        - API Token Management
        - Client Configuration
        - Secure Communication
    """,
    'author': 'AltAVltd',
    'website': 'https://altavltd.com',
    'depends': [
        'mail',
        'base',
        'base_setup',
        'web',
        'project',
        'subscription_package',
        'hr_timesheet'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/task_cron.xml',
        'views/alt_support_views.xml',
        'menus/alt_support_menu.xml',
        'views/task_pop_up.xml',
        'views/subscription_view.xml',
        'views/project_task_portal.xml',
        'views/task_view.xml',
        'views/alt_hr_timesheet_portal_templates.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'alt_support_bridge_server/static/src/js/**/*',
            'alt_support_bridge_server/static/src/css/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} 
# -*- coding: utf-8 -*-
{
    'name': "Local Video Snippet",
    'version': '1.1',
    'author': "OuMai Software Pvt. Ltd.",
    'category': 'Website',
    'website': "https://www.luomt.com",
    'license': 'OPL-1',
    'description': """
        Provide Local video as a Snippet on your Website.
    """,
    'summary': '''
        Local Video Snippet allows you to upload local video for content snippet on website. 
    ''',
    'images': ['static/description/banner.gif'],
    'depends': ['base','web','website','web_editor'],
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
    'price': 2.6,
    'currency': 'USD',
    'demo': [],
    'assets':{
        'web.assets_backend':[],
        'web.assets_frontend':[
            'lv_snp/static/src/scss/main.scss',
            'lv_snp/static/src/components/video_player.js',
        ],
        'web_editor.assets_media_dialog': [
            'lv_snp/static/src/components/video_selector_in.xml',
            'lv_snp/static/src/components/video_selector_in.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False
}

